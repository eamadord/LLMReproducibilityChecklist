from pipeline import scrap_neurips
from pipeline import parse_results
from pipeline import evaluate_results
from pipeline import retrieve_LLM_checklist
from pipeline import utils
import argparse

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--model','-m', help="Select the LLM model to compare: llama-3/gpt-3.5-turbo/deepseek-r1. Default is all",default='llama-3')
    parser.add_argument('--plot','-p',help="Plot final results",default=True)

    args=parser.parse_args()
    model=args.model
    plot=args.plot
    pdf_files=args.pdf_files
    json_files=args.json_files

    print('===== 🔎 Scrapping NeurIPS data =====')
    scrap_neurips.extraction_pipeline()
    print('===== 🤖 Generating LLM checklists =====')
    if model=='llama-3':
        retrieve_LLM_checklist.llm_llama3()
    elif model=='gpt-3.5-turbo':
        retrieve_LLM_checklist.llm_gpt35_checklist()
    elif model=='deepseek-r1':
        retrieve_LLM_checklist.llm_deepseek()
    else:
        retrieve_LLM_checklist.llm_gpt35_checklist()
        retrieve_LLM_checklist.llm_llama3()
        retrieve_LLM_checklist.llm_deepseek()
    print('===== 📖 Parsing LLM results =====')
    parse_results.parse_base_checklist()
    if model=='llama-3':
        parse_results.parse_results(model='llama-3')
    elif model=='gpt-3.5-turbo':
        parse_results.parse_results()
    elif model=='deepseek-r1':
        parse_results.parse_results(model='deepseek-r1')
    else:
        parse_results.parse_all_results()

    if plot:
        print('===== 🧮 Plotting results =====')
        evaluate_results.plot_data()