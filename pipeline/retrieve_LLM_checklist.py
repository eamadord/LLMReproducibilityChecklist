from pypdf import PdfReader
import os
import shutil
from langchain_community.llms import Ollama
import utils

os.environ['OPENAI_API_KEY']="OPENAI_API_KEY" #Replace by OpenAI key

corrupted_pdfs=["084727e8abf90a8365b940036329cb6f-Paper-Conference","868f2266086530b2c71006ea1908b14a-Paper-Conference","880d8999c07a8efc9bbbeb0c38f50765-Paper-Conference","948552777302d3abf92415b1d7e9de70-Paper-Conference",
                "a995960dd0193654d6b18eca4ac5b936-Paper-Conference","acbfe708197ff78ad04cc1beb1710979-Paper-Conference","b528459c99e929718a7d7e1697253d7f-Paper-Conference","b8bf2c0dd0b48511889b7d3b2c5fc8f5-Paper-Conference",
                "38e511a690709603d4cc3a1c52b4a9fd-Paper-Conference","6489f2c6ac6420124fcef2a489615a97-Paper-Conference","66f7a3df255c47b2e72f30b310a7e44a-Paper-Conference","95c6ae3f3393786203a4b6dcb9df1036-Paper-Conference",
                "3743e69c8e47eb2e6d3afaea80e439fb-Paper-Conference","572aaddf9ff774f7c1cf3d0c81c7185b-Paper-Conference","620317fb69899dbf58798d242a58d351-Paper-Conference","9bf0810a4a1597a36d27ceea58667d92-Paper-Conference",
                "04bd683d5428d91c5fbb5a7d2c27064d-Paper-Conference","0073cc73e1873b35345209b50a3dab66-Paper-Conference","215aeb07b5996c969c0123c3c6ee8f54-Paper-Conference","2d76b6a9f96181ab717c1a15ab9302e1-Paper-Conference",
                "bc18c538d983cea434f9281148d43e1e-Paper-Conference","bd8b52c2fefdb37e3b3953a37408e9dc-Paper-Conference","d68b4e80fd0dd8ac72092b3acd418f75-Paper-Conference","d78ece6613953f46501b958b7bb4582f-Paper-Conference",
                "dfa1106ea7065899b13f2be9da04efb4-Paper-Conference","ef0af61ccfba2bf9fad4f4df6dfcb7c3-Paper-Conference"] #List of downloaded PDFs with corruption issues

def llm_gpt35_checklist(filename='NeurIPS_papers'):
    print('---> Processing papers with GPT-3.5-turbo')
    papers= utils.load_obj(os.path.join('../files', filename))
    model_name='gpt-3.5-turbo'
    for k,paper in papers.items():
        if 'pdf_file' in paper.keys():
            url = paper['pdf_file']
            pdf_name = url.split('.')[0]
            if not os.path.isdir(os.path.join('./json_files',model_name)):
                os.mkdir(os.path.join('./json_files',model_name))
            if os.path.isdir(os.path.join('./json_files', pdf_name)):
                continue
            try:
                if not os.path.isfile(os.path.join('pdf_files', pdf_name + '.pdf')) or pdf_name in corrupted_pdfs:
                    continue
                reader = PdfReader(os.path.join('pdf_files', pdf_name + '.pdf'))
                text = ""
                for p in range(len(reader.pages)):
                    text += str(reader.pages[p].extract_text())
                with open('tmp.txt', 'w+') as f:
                    f.write(text)
            except TypeError:
                continue
            # first evaluation:
            os.system(
                f"""!cat tmp.txt | llm "Check whether the attached file meets the points on this checklist. Return the results in JSON format, where for each point in the checklist report whether it is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field called 'evidence'. Checklist: -Do the main claims made in the abstract and introduction accurately reflect the paper's contributions and scope? -Does the paper describe the limitations of the work? -Does the paper discuss any potential negative societal impacts of your work? -Does the paper address the etichs review guidelines?" -m {model_name} > authors_results.json""")
            # second evaluation:
            os.system(
                f"""!cat tmp.txt | llm "Check whether the attached file meets the points on this checklist. Return the results in JSON format, where for each point in the checklist report whether it is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field called 'evidence'. Checklist: -Does the paper state the full set of assumptions of all theoretical results? -Does the paper include complete proofs of all theoretical results" -m {model_name} > theoretical_results.json""")
            # third evaluation:
            os.system(
                f"""!cat tmp.txt | llm "Check whether the attached file meets the points on this checklist. Return the results in JSON format, where for each point in the checklist report whether it is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field named 'evidence'. Checklist: -Does the paper include the code, data, and instructions needed to reproduce the main experimental results? -Are all the training details specified? -Are error bars reported? -Is the total amound of compute and the type of resources used included in the paper" -m {model_name} > experiments_results.json""")
            # fourth evaluation:
            os.system(
                f"""!cat tmp.txt | llm "Check whether the attached file meets the points on this checklist. Return the results in JSON format, where for each point in the checklist report whether it is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field named 'evidence'. Checklist: -If the work references existing assets, are these assets properly cited? -Is the license of the assets mentioned? -Are new assets included either in the suplemental material or in the URL? -Does the paper discuss whether and how the consent was obtained from people whose data is used/curated? -Does the paper discuss whether the data used/curated contains personally identifiable information or offensive content?" -m {model_name} > assets_results.json""")
            os.remove('tmp.txt')
            os.mkdir(os.path.join('./json_files',model_name, pdf_name))
            shutil.move('authors_results.json', os.path.join('./json_files',model_name, pdf_name))
            shutil.move('theoretical_results.json', os.path.join('./json_files',model_name, pdf_name))
            shutil.move('experiments_results.json', os.path.join('./json_files',model_name, pdf_name))
            shutil.move('assets_results.json', os.path.join('./json_files',model_name, pdf_name))

def llm_llama3(filename='NeurIPS_papers'):
    print('---> Processing papers with llama-3')
    model_name='Llama-3'
    llm=Ollama(model='llama3')
    papers = utils.load_obj(os.path.join('../files', filename))
    for k,paper in papers.items():
        if 'pdf_file' in paper.keys():
            url = paper['pdf_file']
            pdf_name = url.split('.')[0]
            if os.path.isdir(os.path.join('json_files', model_name, pdf_name)):
                continue
            try:
                if not os.path.isfile(os.path.join('pdf_files', pdf_name + '.pdf')) or pdf_name in corrupted_pdfs:
                    continue
                reader = PdfReader(os.path.join('pdf_files', pdf_name + '.pdf'))
                text = ""
                for p in range(len(reader.pages)):
                    text += str(reader.pages[p].extract_text())
                with open('tmp.txt', 'w+') as f:
                    f.write(text)
            except TypeError:
                continue
            prompt_1 = f"""From this paper {text}, tell me whether it meets the points of the following checklist. Return the results in JSON format, where for each point in the checklist report whether it is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field called 'evidence'. Checklist: -Do the main claims made in the abstract and introduction accurately reflect the paper's contributions and scope? -Does the paper describe the limitations of the work? -Does the paper discuss any potential negative societal impacts of your work? -Does the paper address the etichs review guidelines?"""
            prompt_2 = f"""From this paper {text}, tell me whether it meets the points of the following checklist. Return the results in JSON format, where for each point in the checklist report whether it is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field called 'evidence'. Checklist: -Does the paper state the full set of assumptions of all theoretical results? -Does the paper include complete proofs of all theoretical results"""
            prompt_3 = f"""From this paper {text}, tell me whether it meets the points of the following checklist. Return the results in JSON format, where for each point in the checklist report whether it is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field named 'evidence'. Checklist: -Does the paper include the code, data, and instructions needed to reproduce the main experimental results? -Are all the training details specified? -Are error bars reported? -Is the total amound of compute and the type of resources used included in the paper"""
            prompt_4 = f"""From this paper {text}, tell me whether it meets the points of the following checklist.Return the results in JSON format, where for each point in the checklist report whether it is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field named 'evidence'. Checklist: -If the work references existing assets, are these assets properly cited? -Is the license of the assets mentioned? -Are new assets included either in the suplemental material or in the URL? -Does the paper discuss whether and how the consent was obtained from people whose data is used/curated? -Does the paper discuss whether the data used/curated contains personally identifiable information or offensive content?"""
            # first evaluation:
            response1 = llm.invoke(prompt_1)
            with open('authors_results.json', 'w+') as f:
                f.write(response1)
            # second evaluation:
            response2 = llm.invoke(prompt_2)
            with open('theoretical_results.json', 'w+') as f:
                f.write(response2)
            # third evaluation
            response3 = llm.invoke(prompt_3)
            with open('experiments_results.json', 'w+') as f:
                f.write(response3)
            # fourth evaluation
            response4 = llm.invoke(prompt_4)
            with open('assets_results.json', 'w+') as f:
                f.write(response4)
            os.remove('tmp.txt')
            os.mkdir(os.path.join('json_files', model_name, pdf_name))
            shutil.move('authors_results.json', os.path.join('./json_files',model_name, pdf_name))
            shutil.move('theoretical_results.json', os.path.join('./json_files',model_name, pdf_name))
            shutil.move('experiments_results.json',os.path.join('./json_files',model_name, pdf_name))
            shutil.move('assets_results.json', os.path.join('./json_files',model_name, pdf_name))

def llm_deepseek(filename='NeurIPS_papers'):
    print('---> Processing papers with DeepSeek-R1')
    model_name='deepseek-r1'
    llm=Ollama(model='deepseek-r1')
    papers = utils.load_obj(os.path.join('../files', filename))
    for k, paper in papers.items():
        if 'pdf_file' in paper.keys():
            url = paper['pdf_file']
            pdf_name = url.split('.')[0]
            print(pdf_name)
            if os.path.isdir(os.path.join('json_files', model_name, pdf_name)):
                continue
            try:
                if not os.path.isfile(os.path.join('pdf_files', pdf_name + '.pdf')) or pdf_name in corrupted_pdfs:
                    continue
                reader = PdfReader(os.path.join('pdf_files', pdf_name + '.pdf'))
                text = ""
                for p in range(len(reader.pages)):
                    text += str(reader.pages[p].extract_text())
                with open('tmp.txt', 'w+') as f:
                    f.write(text)
            except TypeError:
                continue
            text = text.split('Checklist')[0]
            prompt_1 = f"""The following text is part of a research article: {text}. From the previouus text, tell me whether it meets the points of the following checklist. Return the results in JSON format, where for each point in the checklist, copy its content in a field called "point", and then report whether the point is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field called 'evidence'. Checklist: -Do the main claims made in the abstract and introduction accurately reflect the paper's contributions and scope? -Does the paper describe the limitations of the work? -Does the paper discuss any potential negative societal impacts of your work? -Does the paper address the etichs review guidelines?"""
            prompt_2 = f"""The following text is part of a research article: {text}. From the previouus text, tell me whether it meets the points of the following checklist. Return the results in JSON format, where for each point in the checklist, copy its content in a field called "point", and then report whether the point is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field called 'evidence'. Checklist: -Does the paper state the full set of assumptions of all theoretical results? -Does the paper include complete proofs of all theoretical results"""
            prompt_3 = f"""The following text is part of a research article: {text}. From the previouus text, tell me whether it meets the points of the following checklist. Return the results in JSON format, where for each point in the checklist, copy its content in a field called "point", and then report whether the point is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field named 'evidence'. Checklist: -Does the paper include the code, data, and instructions needed to reproduce the main experimental results? -Are all the training details specified? -Are error bars reported? -Is the total amound of compute and the type of resources used included in the paper"""
            prompt_4 = f"""The following text is part of a research article: {text}. From the previouus text, tell me whether it meets the points of the following checklist. Return the results in JSON format, where for each point in the checklist, copy its content in a field called "point", and then report whether the point is met fully, partially or not at all in a field called 'score'. Provide evidence for each point as well in another JSON field named 'evidence'. Checklist: -If the work references existing assets, are these assets properly cited? -Is the license of the assets mentioned? -Are new assets included either in the suplemental material or in the URL? -Does the paper discuss whether and how the consent was obtained from people whose data is used/curated? -Does the paper discuss whether the data used/curated contains personally identifiable information or offensive content?"""
            # first evaluation:
            response1 = llm.invoke(prompt_1)
            with open('authors_results.json', 'w+') as f:
                f.write(response1)
            # second evaluation:
            response2 = llm.invoke(prompt_2)
            with open('theoretical_results.json', 'w+') as f:
                f.write(response2)
            # third evaluation
            response3 = llm.invoke(prompt_3)
            with open('experiments_results.json', 'w+') as f:
                f.write(response3)
            # fourth evaluation
            response4 = llm.invoke(prompt_4)
            with open('assets_results.json', 'w+') as f:
                f.write(response4)
            os.remove('tmp.txt')
            os.mkdir(os.path.join('json_files', model_name, pdf_name))
            shutil.move('authors_results.json',  os.path.join('./json_files',model_name, pdf_name))
            shutil.move('theoretical_results.json', os.path.join('./json_files',model_name, pdf_name))
            shutil.move('experiments_results.json',  os.path.join('./json_files',model_name, pdf_name))
            shutil.move('assets_results.json',  os.path.join('./json_files',model_name, pdf_name))

