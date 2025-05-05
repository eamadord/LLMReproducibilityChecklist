from selenium import webdriver
from selenium.webdriver.common.by import By
from pipeline import utils
import os
import requests
from pypdf import PdfReader
import re

options=webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

def scrap_neurips(url='https://papers.nips.cc/paper_files/paper/2022'):
    filename='NeurIPS_papers'
    driver.get(url)
    all_elements = driver.find_elements(By.CLASS_NAME, "conference")
    papers = {}
    for i, e in enumerate(all_elements):
        paper = e.find_element(By.TAG_NAME, "a")
        title = paper.text
        link = paper.get_attribute("href")
        author = e.find_element(By.TAG_NAME, "i").text
        papers[i] = {'link': link, 'title': title, 'author': author}
    for k,v in papers.items():
        link=v['link']
        driver.get(link)
        pdf_link = driver.find_element(By.NAME, "citation_pdf_url")
        pdf = pdf_link.get_attribute("content")
        papers[k].update({'pdf_link': pdf})
        utils.save_obj(papers, os.path.join('../files', filename))

def save_pdf_files(filename='NeurIPS_papers'):
    papers= utils.load_obj(os.path.join('../files', filename))
    for k,v in papers.items():
        if 'pdf_link' in v.keys():
            url=v['pdf_link']
            pdf_name=url.split('/')[-1]
            response=requests.get(url)
            if not os.path.isdir('./pdf_files'):
                os.mkdir('./pdf_files')
            with open(os.path.join('./pdf_files',pdf_name),'wb') as f:
                f.write(response.content)

def extract_checklist(filename='NeurIPS_papers'):
    papers= utils.load_obj(os.path.join('../files', filename))
    for k,v in papers.items():
        if 'pdf_file' in v.keys():
            pdf_file=v['pdf_file']
            pdf_name = pdf_file.split('/')[-1]
            if not os.path.isfile(os.path.join('./pdf_files',pdf_name)):
                continue
            reader=PdfReader(os.path.join('./pdf_files',pdf_name))
            text=""
            for p in range(len(reader.pages)-2, len(reader.pages)):
                text+=str(reader.pages[p].extract_text())
            with open('tmp.txt','w+',encoding='utf-8') as f:
                f.write(text)
            lines=text.split('\n')
            checklist = {
                "authors": {
                    "claims_abstract_intro": "",
                    "limitations": "",
                    "negative_societal_impacts": "",
                    "read_ethics_review": ""
                },
                "theoretical_results": {
                    "assumptions": "",
                    "proof": ""
                },
                "experiments": {
                    "reproducibility": "",
                    "training_details": "",
                    "error_bars": "",
                    "compute_resources": ""
                },
                "assets": {
                    "existing_assets": "",
                    "license_assets": "",
                    "new_assets": "",
                    "consent": "",
                    "identifiable_information": ""
                },
                "human_subjects": {
                    "instructions": "",
                    "risks": "",
                    "compensation": ""
                }
            }
            cur_stage = {}
            filling = False
            cur_key = ""
            cur_subkey = ""
            for l in lines:
                # Check with checklist we're filling
                if 'authors' in l and '...' in l:
                    cur_key = "authors"
                    filling = True
                elif 'theoretical results' in l and '...' in l:
                    cur_key = 'theoretical_results'
                    filling = True
                elif 'experiments' in l and '...' in l:
                    cur_key = 'experiments'
                    filling = True
                elif 'assets' in l and '...' in l:
                    cur_key = 'assets'
                    filling = True
                elif 'human' in l and '...' in l:
                    cur_key = 'human_subjects'
                    filling = True
                # Filling checklists
                elif filling:
                    if cur_key == 'authors':
                        if 'claims' in l:
                            cur_subkey = 'claims_abstract_intro'
                        elif 'limitations' in l:
                            cur_subkey = 'limitations'
                        elif 'impacts' in l:
                            cur_subkey = 'negative_societal_impacts'
                        elif 'ethics' in l:
                            cur_subkey = 'read_ethics_review'
                    elif cur_key == 'theoretical_results':
                        if 'assumptions' in l:
                            cur_subkey = 'assumptions'
                        elif 'proofs' in l:
                            cur_subkey = 'proof'
                    elif cur_key == 'experiments':
                        if 'reproduce' in l:
                            cur_subkey = 'reproduce'
                        elif 'training' in l:
                            cur_subkey = 'training_details'
                        elif 'error' in l:
                            cur_subkey = 'error_bars'
                        elif 'compute' in l:
                            cur_subkey = 'compute_resources'
                    elif cur_key == 'assets':
                        if 'existing' in l:
                            cur_subkey = 'existing_assets'
                        elif 'license' in l:
                            cur_subkey = 'license_assets'
                        elif 'supplemental' in l:
                            cur_subkey = 'new_assets'
                        elif 'consent' in l:
                            cur_subkey = 'consent'
                        elif 'identifiable' in l:
                            cur_subkey = 'identifiable_information'
                    elif cur_key == 'human_subjects':
                        if 'instructions' in l:
                            cur_subkey = 'instructions'
                        elif 'risks' in l:
                            cur_subkey = 'risks'
                        elif 'wage' in l:
                            cur_subkey = 'compensation'
                    if '[' in l:
                        match = re.search(r"\[(.*?)\]", l)
                        response = match.group(1)
                        checklist[cur_key][cur_subkey] = response
                elif "Checklist" not in l and not filling:
                    continue
            os.remove('tmp.txt')
            papers[k].update({'checklist': checklist})
        utils.save_obj(papers, os.path.join('../files', filename))

def extraction_pipeline():
    scrap_neurips()
    print('---> Storing PDF Files')
    save_pdf_files()
    print('---> Extracting author checklist')
    extract_checklist()

