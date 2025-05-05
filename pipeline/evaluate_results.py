from pipeline import utils
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

def _clean_scorefile(score_dict=None,score_checklist='score_checklist'):
    if score_checklist:
        scores=utils.load_obj(os.path.join('./files',score_checklist))
    else:
        scores=score_dict
    clean_entries={}
    for k,v in scores.items():
        if len(v)==4:
            clean_entries[k]=v
    return clean_entries

def _simplify_values(text):
    if isinstance(text,int) or isinstance(text,float):
        if text==1:
            return 'Yes'
        else:
            return 'No'
    elif text is None:
        return 'No'
    elif not text:
        return 'No'
    elif 'fully' in text.lower() or 'partially' in text.lower():
        return 'Yes'
    elif 'not' in text.lower() or 'no' in text.lower() or 'n/a' in text.lower():
        return 'No'
    else:
        return text

def _process_scores(score_dict):
    parsed_dict={}
    for k,v in score_dict.items():
        parsed_dict[k]={}#Main file
        for i,j in v.items():
            clean_results={}
            for c,e in j.items():
                entry= {kk:_simplify_values(vv) for kk,vv in e.items()}
                clean_results[c]=entry
            parsed_dict[k].update({i:clean_results})
    return parsed_dict

def _count_similarity(base,values):
    count=0
    for k,v in base.items():
        if values[k]==v:
            count+=1
    return float(count/len(base))

def plot_data(score_file='score_checklist',process=True):
    if process:
        parsed_dict=_clean_scorefile(score_file)
        parsed_dict=_process_scores(parsed_dict)
    else:
        parsed_dict=utils.load_obj(os.path.join('./files',score_file))
    base={}
    results=_section_comparison(parsed_dict)
    section='assets'
    results_author=_field_comparison(parsed_dict,section)
    _plot_comparison_field(results_author,section)


def _section_comparison(data, ref_model='base'):
    count = defaultdict(lambda: defaultdict(lambda: [0, 0]))

    for root_key in data:
        print(root_key)
        models = data[root_key].keys()
        if ref_model not in models:
            continue

        for model in models:
            if model == ref_model:
                continue
            for section in data[root_key][ref_model]:
                for field in data[root_key][ref_model][section]:
                    ref_value = data[root_key][ref_model][section][field]
                    if field not in data[root_key][model][section]:
                        continue
                    modelo_value = data[root_key][model][section][field]
                    count[model][section][1] += 1
                    if ref_value == modelo_value:
                        count[model][section][0] += 1
    results = {}
    for model in count:
        results[model] = {}
        for section in count[model]:
            check, total = count[model][section]
            acc = 100 * check / total if total > 0 else 0
            results[model][section] = round(acc, 1)

    df_result = pd.DataFrame(results).T
    return df_result

def _plot_section_comparison(df_result):

    df_long = df_result.reset_index().melt(id_vars='index', var_name='Section', value_name='Coincidence (%)')
    df_long = df_long.rename(columns={'index': 'Model'})


    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_long, x='Section', y='Coincidence (%)', hue='Model', palette='Set2')

    plt.title('Coincidence w.r.t author checklist per model')
    plt.ylabel('Coincidencia (%)')
    plt.xlabel('Section')
    plt.ylim(0, 100)
    plt.legend(title='Model', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()


def _field_comparison(data, section, ref_model='base'):
    count = defaultdict(dict)

    for root_key in data:
        models = data[root_key].keys()
        if ref_model not in models:
            continue

        for model in models:
            if model == ref_model:
                continue

            for field in data[root_key][ref_model].get(section, {}):
                ref_value = data[root_key][ref_model][section][field]
                modelo_value = data[root_key][model].get(section, {}).get(field)
                #key = (model, field)
                if field not in count[model]:
                    count[model][field] = [0, 0]
                count[model][field][1] += 1  # total
                if ref_value == modelo_value:
                    count[model][field][0] += 1  # acierto

    # Crear DataFrame con porcentaje de acierto por campo
    results = []
    for model in count:
        for field in count[model]:
            if section=='assets' and field=='proof':
                continue
            if section=='experiments' and field=='reproduce':
                continue
            checks, total = count[model][field]
            per = 100 * checks / total if total > 0 else 0
            results.append({'Model': model, 'Question': field, 'Coincidence (%)': round(per, 1)})

    return pd.DataFrame(results)

def _plot_comparison_field(df, section):
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x='Question', y='Coincidence (%)', hue='Model', palette='icefire')
    plt.title(f'Coincidence w.r.t author checklist per question in "{section}"')
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.show()