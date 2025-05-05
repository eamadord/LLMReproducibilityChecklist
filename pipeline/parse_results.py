import json
import os

import llm

from pipeline import utils
import re
from collections import defaultdict

template_checklist="""{
          "authors":{
            "claims_abstract_intro":"",
            "limitations":"",
            "negative_societal_impacts":"",
            "read_ethics_review":""
          },
        "th_results":{
            "assumptions":"",
            "proof":""
        },
            "experiments":{
                "reproducibility":"",
                "training_details":"",
                "error_bars":"",
                "compute_resources":""
            },
            "assets":{
                "existing_assets":"",
                "license_assets":"",
                "new_assets":"",
                "consent":"",
                "identifiable_information":""
            }
        }"""

def _extract_json_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    # Expresión regular para encontrar contenido entre ''' y '''
    matches = re.findall(r"```(.*?)```", content, re.DOTALL)
    matches = matches[0]
    json_data=json.loads(matches)
    return json_data

def _merge_duplicate_keys(obj):
    """ Reorganiza un diccionario para convertir claves duplicadas en listas. """
    new_dict = defaultdict(list) #Here there was a key
    for key, value in obj.items():
        if key in new_dict:
            # Si la clave ya existe, agregamos el nuevo valor a una lista
            if isinstance(new_dict[key], list):
                new_dict[key].append(value)
            else:
                new_dict[key] = [new_dict[key], value]
        else:
            new_dict[key] = value

    # Convertimos listas de un solo elemento en valores simples
        return {k: v if not isinstance(v, list) or len(v) < 1 else v[0] for k, v in new_dict.items()}



def _fix_json_structure(json_string):
    try:
        # Cargar JSON normalmente
        return json.dumps(json.loads(json_string), indent=2)
    except json.JSONDecodeError:
        pass  # Si falla, intentamos corregirlo

    fixed_dict = {}
    stack = [{}]  # Usamos una pila para mantener la estructura del JSON
    current_obj = stack[-1]

    # Procesar línea por línea para reconstruir manualmente el JSON
    for line in json_string.strip().splitlines():
        line = line.strip().rstrip(',')

        if line.startswith("{") or line.startswith("}"):
            continue

        try:
            key, value = line.split(":", 1)
            key = key.strip().strip('"')
            value = value.strip().rstrip(',')

            # Intentamos parsear el valor como JSON
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = value.strip('"')

            if key in current_obj:
                if not isinstance(current_obj[key], list):
                    current_obj[key] = [current_obj[key]]
                current_obj[key].append(value)
            else:
                current_obj[key] = value
        except ValueError:
            pass  # Ignorar líneas mal formateadas

    fixed_dict = _merge_duplicate_keys(current_obj)

    return json.dumps(fixed_dict, indent=2)


def _fix_malformed_json(json_text):
    """Fixes malformed JSON responses from deepseek"""

    json_text = json_text.strip()

    matches = re.findall(r'\{[^{}]*\}', json_text, re.DOTALL)

    if not matches:
        return {}

    fixed_json = f"[{','.join(matches)}]"

    try:
        return json.loads(fixed_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al procesar JSON: {e}")

def _extract_json(text):
    """Extrae y carga la parte JSON válida de un texto."""
    try:
        matches = re.search(r'(\{.*\})', text, re.DOTALL)
        if matches:
            json_text = matches.group(1)
            try:
              json_data=json.loads(json_text)
            except:
              json_data=_fix_malformed_json(json_text)

            return json_data
        else:
            _fix_malformed_json(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al cargar JSON: {e}")

def _extract_json_deepseek_r1(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    json_data = _extract_json(content)
    return json_data

def parse_base_checklist(input_filename='NeurIPS_papers',out_filename='parsed_checklist'):
    papers=utils.load_obj(os.path.join('./files',input_filename))
    results_per_paper={}
    for k,v in papers.items():
        base_checklist=v['checkist']
        url=v['pdf_file']
        pdf_name=url.split('.')[0]
        results_per_paper[pdf_name]={'base':{'authors':base_checklist['authors'],'th_results':base_checklist['theoretical_results'],
                                'experiments':base_checklist['experiments'],'assets':base_checklist['assets']}}
    utils.save_obj(results_per_paper,os.path.join('./files',out_filename))

def _parse_authors(content,cur_list,list_name=''):
    terms_mapping={
        'claim':['claim','abstract','1a'],
        'limitations':['limitations','1b'],
        'negative':['negative','impact','1c'],
        'ethics':['ethics','ethical','1d']
    }
    if isinstance(content, dict) and len(content.keys()) == 1:
        author_dict = content[list_name]
        if isinstance(author_dict, list):
            for i, e in enumerate(author_dict):
                if len(e) == 1:
                    for kk, ee in e.items():
                        if any(term in kk for term in terms_mapping['claim']):
                            cur_list['claims_abstract_intro'] = ee['score']
                        elif any(term in kk for term in terms_mapping['limitations']):
                            cur_list['limitations'] = ee['score']
                        elif any(term in kk for term in terms_mapping['negative']):
                            cur_list['negative_societal_impacts'] = ee['score']
                        elif any(term in kk for term in terms_mapping['ethics']):
                            cur_list['read_ethics_review'] = ee['score']
                else:
                    if 'evidence' not in e.keys():
                        continue
                    elif any(term in e.keys() for term in terms_mapping['claim']) or 'abstract' in e['evidence']:
                        if 'score' in e.keys():
                            cur_list['claims_abstract_intro'] = e['score']
                    elif any(term in e.keys() for term in terms_mapping['limitations']) or 'limitations' in e['evidence']:
                        if 'score' in e.keys():
                            cur_list['limitations'] = e['score']
                    elif any(term in e.keys() for term in terms_mapping['negative']) or 'negative' in e['evidence']:
                        if 'score' in e.keys():
                            cur_list['negative_societal_impacts'] = e['score']
                    elif any(term in e.keys() for term in terms_mapping['ethics']) or 'ethics' in e['evidence']:
                        if 'score' in e.keys():
                            cur_list['read_ethics_review'] = e['score']
        elif isinstance(author_dict, dict):
            for kk, e in author_dict.items():
                if not isinstance(e, dict): continue
                if any(term in kk for term in terms_mapping['claim']) and 'score' in e.keys():
                    cur_list['claims_abstract_intro'] = e['score']
                elif any(term in kk for term in terms_mapping['limitations']) and 'score' in e.keys():
                    cur_list['limitations'] = e['score']
                elif any(term in kk for term in terms_mapping['negative']) and 'score' in e.keys():
                    cur_list['negative_societal_impacts'] = e['score']
                elif any(term in kk for term in terms_mapping['ethics']) and 'score' in e.keys():
                    cur_list['read_ethics_review'] = e['score']
    elif isinstance(content, dict) and len(content.keys()) > 1:
        author_dict = content
        for kk, e in author_dict.items():
            if not isinstance(e, dict):
                continue
            if any(term in kk for term in terms_mapping['claim']) and 'score' in e.keys():
                cur_list['claims_abstract_intro'] = e['score']
            elif any(term in kk for term in terms_mapping['limitations']) and 'score' in e.keys():
                cur_list['limitations'] = e['score']
            elif any(term in kk for term in terms_mapping['negative']) and 'score' in e.keys():
                cur_list['negative_societal_impacts'] = e['score']
            elif any(term in kk for term in terms_mapping['ethics']) and 'score' in e.keys():
                cur_list['read_ethics_review'] = e['score']
    return cur_list


def _parse_th_results(content, cur_list,list_name):
    if isinstance(content, dict) and len(content.keys()) == 1:
        th_dict_tmp = content[list_name]
        th_dict = {}
        if isinstance(th_dict_tmp, list):
            for item in th_dict_tmp:
                if 'point' in item.keys():
                    name = item['point']
                elif 'question' in item.keys():
                    name = item['question']
                elif 'description' in item.keys():
                    name=item['description']
                elif 'text' in item.keys():
                    name=item['text']
                elif 'evidence' in item.keys():
                    name = item['evidence']
                else:
                    try:
                        key = list(item.keys())[0]
                        name = item[key]['evidence']
                    except:
                        break
                th_dict[name] = item
        else:
            th_dict = th_dict_tmp
        for i, j in th_dict.items():
            if not isinstance(j, dict) or not j:
                continue
            if not isinstance(i, str):
                i = j['evidence']
            if 'score' not in j.keys():
                key = list(j.keys())[0]
                j = j[key]
            if not isinstance(j, dict): continue
            if 'assumptions' in i and 'score' in j.keys():
                cur_list['assumptions'] = j['score']
            elif 'proof' in i and 'score' in j.keys():
                cur_list['proof'] = j['score']
    elif isinstance(content, dict) and len(content.keys()) > 1:
        for kk, e in content.items():
            if not e or not isinstance(e,dict):
                continue
            if 'assumptions' in kk and 'score' in e.keys():
                cur_list['assumptions'] = e['score']
            elif 'proof' in kk and 'score' in e.keys():
                cur_list['proof'] = e['score']
    return cur_list

def _parse_experiments(content,cur_list,list_name):
    terms_mapping={
        'reproduce':['reproduce','instructions'],
        'training':['training'],
        'error':['error bars','bars'],
        'resources':['resources']
    }
    if isinstance(content, dict) and len(content.keys()) == 1:
        r_dict_tmp = content[list_name]
        r_dict = {}
        if isinstance(r_dict_tmp, list):
            for item in r_dict_tmp:
                if 'point' in item.keys():
                    name = item['point']
                elif 'check' in item.keys():
                    name = item['check']
                elif 'text' in item.keys():
                    name = item['text']
                elif 'evidence' in item.keys():
                    name = item['evidence']
                else:
                    break
                if not isinstance(name,str):
                    break
                r_dict[name] = item
            for i, j in r_dict.items():
                if not isinstance(j, dict): continue
                if any(term in i for term in terms_mapping['reproduce']) and 'score' in j.keys():
                    cur_list['reproducibility'] = j['score']
                elif any(term in i for term in terms_mapping['training']) and 'score' in j.keys():
                    cur_list['training_details'] = j['score']
                elif any(term in i for term in terms_mapping['error']) and 'score' in j.keys():
                    cur_list['error_bars'] = j['score']
                elif any(term in i for term in terms_mapping['resources']) and 'score' in j.keys():
                    cur_list['compute_resources'] = j['score']
        elif isinstance(r_dict_tmp, dict):
            for i, j in r_dict_tmp.items():
                if not isinstance(j, dict): continue
                if any(term in i for term in terms_mapping['reproduce']) and 'score' in j.keys():
                    cur_list['reproducibility'] = j['score']
                elif any(term in i for term in terms_mapping['training']) and 'score' in j.keys():
                    cur_list['training_details'] = j['score']
                elif any(term in i for term in terms_mapping['error']) and 'score' in j.keys():
                    cur_list['error_bars'] = j['score']
                elif any(term in i for term in terms_mapping['resources']) and 'score' in j.keys():
                    cur_list['compute_resources'] = j['score']
        elif isinstance(r_dict, dict):
            for i, j in r_dict_tmp.items():
                if not isinstance(j, dict): continue
                if any(term in i for term in terms_mapping['reproduce']) and 'score' in j.keys():
                    cur_list['reproducibility'] = j['score']
                elif any(term in i for term in terms_mapping['training']) and 'score' in j.keys():
                    cur_list['training_details'] = j['score']
                elif any(term in i for term in terms_mapping['error']) and 'score' in j.keys():
                    cur_list['error_bars'] = j['score']
                elif any(term in i for term in terms_mapping['resources']) and 'score' in j.keys():
                    cur_list['compute_resources'] = j['score']

    elif isinstance(content, dict) and len(content.keys()) > 1:
        for i, j in content.items():
            if not isinstance(j, dict): continue
            if any(term in i for term in terms_mapping['reproduce']) and 'score' in j.keys():
                cur_list['reproducibility'] = j['score']
            elif any(term in i for term in terms_mapping['training']) and 'score' in j.keys():
                cur_list['training_details'] = j['score']
            elif any(term in i for term in terms_mapping['error']) and 'score' in j.keys():
                cur_list['error_bars'] = j['score']
            elif any(term in i for term in terms_mapping['resources']) and 'score' in j.keys():
                cur_list['compute_resources'] = j['score']
    elif isinstance(content, list) and len(content) > 1:
        for i, j in enumerate(content):
            if not j or 'evidence' not in j.keys() or 'score' not in j.keys() or not j['evidence']:
                continue
            if any(term in j['evidence'] for term in terms_mapping['reproduce']):
                cur_list['reproducibility'] = j['score']
            elif any(term in j['evidence'] for term in terms_mapping['training']):
                cur_list['training_details'] = j['score']
            elif any(term in j['evidence'] for term in terms_mapping['error']):
                cur_list['error_bars'] = j['score']
            elif any(term in j['evidence'] for term in terms_mapping['resources']):
                cur_list['compute_resources'] = j['score']
    return cur_list
def _parse_assets(content, cur_list, list_name):
    as_dict = {}
    as_dict_tmp = content
    terms_mapping={
        'references':['references','1'],
        'license':['license','2'],
        'new_assets':['new','assets','3'],
        'identifiable':['identifiable','information','privacy','4'],
        'consent':['consent','5']
    }
    if isinstance(content, dict) and len(content.keys()) == 1:
        as_dict_tmp = content[list_name]
        if isinstance(as_dict_tmp, list):
            for item in as_dict_tmp:
                if 'criteria' in item.keys():
                    name = item['criteria']
                elif 'point' in item.keys():
                    name = item['point']
                elif 'content' in item.keys():
                    name = item['content']
                elif 'Evidence' in item.keys():
                    name = item['Evidence']
                else:
                    name = item['evidence']
                if isinstance(name, list):
                    name = name[0]
                if isinstance(name, dict):
                    l_name = list(name.keys())[0]
                    name = name[l_name]
                as_dict[name] = item
            for i, j in as_dict.items():
                if any(term in i for term in terms_mapping['references']) and 'score' in j.keys():
                    cur_list['existing_assets'] = j['score']
                elif any(term in i for term in terms_mapping['license']) and 'score' in j.keys():
                    cur_list['license_assets'] = j['score']
                elif any(term in i for term in terms_mapping['new_assets']) and 'score' in j.keys():
                    cur_list['new_assets'] = j['score']
                elif any(term in i for term in terms_mapping['identifiable']) and 'score' in j.keys():
                    cur_list['identifiable_information'] = j['score']
                elif any(term in i for term in terms_mapping['consent']) and 'score' in j.keys():
                    cur_list['consent'] = j['score']
    if isinstance(content, dict) and len(content.keys()) > 1 or isinstance(as_dict_tmp, dict):
        for kk, e in content.items():
            if not isinstance(e, dict): continue
            if any(term in kk for term in terms_mapping['references']) and 'score' in e.keys():
                cur_list['existing_assets'] = e['score']
            elif any(term in kk for term in terms_mapping['license']) and 'score' in e.keys():
                cur_list['license_assets'] = e['score']
            elif any(term in kk for term in terms_mapping['new_assets']) and 'score' in e.keys():
                cur_list['new_assets'] = e['score']
            elif any(term in kk for term in terms_mapping['identifiable']) and 'score' in e.keys():
                cur_list['identifiable_information'] = e['score']
            elif any(term in kk for term in terms_mapping['consent'])and 'score' in e.keys():
                cur_list['consent'] = e['score']
    return cur_list


def parse_results(model='gpt-3.5-turbo',checklist_file='parsed_checklist',score_checklist='score_checklist'):
    print('---> Parsing results for %s' %model)
    if os.path.isfile(os.path.join('./files',score_checklist+'.pkl')):
        parsed_results_per_paper=utils.load_obj(os.path.join('./files',score_checklist))
    else:
        parsed_results_per_paper = {}
    results_per_paper = utils.load_obj(os.path.join('./files', checklist_file))
    for paper_name, checklists in results_per_paper.items():
        print(paper_name)
        if 'base' not in parsed_results_per_paper[paper_name].keys():
            parsed_results_per_paper[paper_name] = {'base': checklists['base']}
        parsed_results_gpt35 = '%s' %template_checklist
        parsed_results_gpt35 =json.loads(parsed_results_gpt35)
        if not model in checklists.keys():
            continue
        results = checklists[model]
        list_name=""
        for k, v in results.items():
            if isinstance(v,dict) and len(list(v.keys())) == 1:
                list_name = list(v.keys())[0]
            elif isinstance(v,list) and len(v)==1:
                v=v[0]
            if k=="authors":
                cur_list=parsed_results_gpt35[k]
                fill_list=_parse_authors(v,cur_list,list_name)
            elif k == 'th_results':
                cur_list = parsed_results_gpt35[k]
                fill_list= _parse_th_results(v,cur_list,list_name)
            elif k == 'experiments':
                cur_list = parsed_results_gpt35[k]
                fill_list=_parse_experiments(v,cur_list,list_name)
            elif k == 'assets':
                cur_list = parsed_results_gpt35[k]
                fill_list = _parse_assets(v,cur_list,list_name)
            parsed_results_gpt35[k].update(fill_list)
        parsed_results_per_paper[paper_name][model] = parsed_results_gpt35
    utils.save_obj(parsed_results_per_paper,os.path.join('./files',score_checklist))

def parse_all_results():
    #Reading json files
    #parse_base_checklist()
    #parse_gpt35_turbo()
    #parse_llama3()
    #parse_deepseekr1()
    #Parsing results
    parse_results()
    parse_results(model="llama-3")
    parse_results(model="deepseek-r1")



