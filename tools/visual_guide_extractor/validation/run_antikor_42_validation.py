"""Deterministic Sprint 21 dataset builder and live validator."""
from __future__ import annotations
import argparse, asyncio, json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT/"backend"))
from app.core.config import get_settings
from app.embedding.ollama_embedding import OllamaEmbeddingProvider
from app.prompt.prompt_builder import PromptBuilder
from app.providers.ollama_provider import OllamaProvider
from app.retrieval.intent import IntentClassifier
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_provider import ChromaVectorStoreProvider

GUIDES=ROOT/"knowledge_base/guides/antikor_v2"
DATASET=Path(__file__).with_name("antikor_42_validation_dataset.json")
SPRINT=os.getenv("VALIDATION_SPRINT","sprint21")
OUT=ROOT/"work/visual_guide_extraction"/SPRINT
REPORT=OUT/("full_validation_after_recovery.json" if SPRINT=="sprint22" else "full_42_guide_validation.json")
TITLE=re.compile(r"^#\s+(.+?)\s*$",re.M); HEADING=re.compile(r"^##\s+(.+?)\s*$",re.M)
SOURCE=re.compile(r"^-\s+Sayfa:\s+(\S+)",re.M); LABEL=re.compile(chr(96)+"([^"+chr(96)+"]+)"+chr(96))
LIST=re.compile(r"^(?:\d+\.|-)\s+(.+?)\s*$",re.M)
ANSWER_LABEL=re.compile(chr(96)+"([^"+chr(96)+"]{2,80})"+chr(96)+r"\s+(?:buton|düğme|alan|menü)",re.I)
LIMITS=("bilgi bulunamadı","açıkça yer almıyor","mevcut değil","yer almamaktadır","belirtilmemiş")
CRITICAL=(
("c-hedef","Yeni bir güvenlik kuralı oluştururken hedef IP adresini hangi alana girmeliyim?","field_listing","guides/antikor_v2/guvenlik_kurallari/guvenlik-kurallari.md","Alanlar",["Hedef Adres"],["Top 10 Hedef IP","SDWAN","VPN"]),
("c-dnat","Dinamik NAT nasıl oluşturulur?","procedure","guides/antikor_v2/nat/dinamik-nat.md","Kullanım adımları",["Durum","Kaynak Arayüz","Kaydet"],[]),
("c-gk-nav","Güvenlik Kuralları ekranına nasıl giderim?","navigation","guides/antikor_v2/guvenlik_kurallari/guvenlik-kurallari.md","Menü yolu",["Güvenlik Kuralları"],["Sertifika Yönetimi","Top 10 Hedef IP"]),
("c-nat-first","Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?","first_action","guides/antikor_v2/nat/dinamik-nat.md","Görünür kontroller",["+ Ekle"],["VPN","Sertifika"]),
("c-user","Yönetim paneline yeni kullanıcı nasıl eklenir?","procedure","guides/antikor_v2/kullanici_yonetimi/yonetim-paneli-kullanicilari.md","Kullanım adımları",["+ Ekle","Kullanıcı Adı","Kaydet"],[]),
("c-ssl-nav","SSL VPN ayarları hangi menü altında?","navigation","guides/antikor_v2/vpn/ssl-vpn-ayarlari.md","Menü yolu",["VPN Yönetimi","SSL VPN Ayarları"],["Sertifika Yönetimi","İstemcisiz SSL Web VPN"]),
("c-gk-fields","Güvenlik Kuralları ekranında hangi alanları doldurmam gerekiyor?","field_listing","guides/antikor_v2/guvenlik_kurallari/guvenlik-kurallari.md","Alanlar",["Durum","Hedef Adres"],[]),
("c-ipsec","IPSec VPN profili nasıl oluşturulur?","procedure","guides/antikor_v2/vpn/ipsec-vpn-profilleri.md","Kullanım adımları",["+ Ekle","Profil Adı"],[]),
("c-compare","IPSec VPN ile SSL VPN arasındaki fark nedir?","comparison","guides/antikor_v2/vpn/ipsec-vpn-ayarlari.md","Kapsam",["IPSec VPN","SSL VPN"],[]))

def sections(text):
    found=list(HEADING.finditer(text))
    return {m.group(1).strip():text[m.end():(found[i+1].start() if i+1<len(found) else len(text))].strip() for i,m in enumerate(found)}
def clean(value): return re.sub(r"\s+"," ",re.sub(r"\s*\([^)]*\):.*$","",value)).strip(" .:;-")
def labels(value):
    raw=LABEL.findall(value) or LIST.findall(value)
    return list(dict.fromkeys(x for item in raw if (x:=clean(item))))
def procedure_labels(value):
    found=LABEL.findall(value)
    pattern=re.compile(r"^(.{2,60}?)\s+(?:alanına|alanını|seçeneğini|butonuna|tabını|durumunu|modunu|türünü|adını)\b",re.I)
    for line in LIST.findall(value):
        match=pattern.search(clean(line))
        if match: found.append(clean(match.group(1)))
    found=list(dict.fromkeys(x for x in found if 1<len(x)<=60))
    if found:
        return [
            item for item in found
            if not any(
                item.casefold() != other.casefold()
                and item.casefold() in other.casefold()
                for other in found
            )
        ]
    steps=[clean(x) for x in LIST.findall(value) if clean(x)]
    return [" ".join(item.split()[:4]).strip(" .") for item in steps[:2]+steps[-1:] if item]
def first_menu_path(value,title=""):
    items=LABEL.findall(value) or [clean(x) for x in LIST.findall(value) if clean(x)]
    paths=[x for x in items if ">" in x]
    title_paths=[x for x in paths if x.casefold().startswith(title.casefold())]
    if title_paths: return min(title_paths,key=len)
    if paths: return paths[0]
    return items[0] if items else clean(value.splitlines()[0] if value.splitlines() else value)
def menu_terms(value,title):
    path=first_menu_path(value,title)
    parts=[clean(x) for x in path.split(">") if clean(x)]
    return [x for x in parts if len(x)<=60][:2] or [" ".join(path.split()[:4])]
def scope_terms(title,value):
    folded=value.casefold()
    terms=[x.strip("/-") for x in title.split() if len(x.strip("/-"))>=3 and x.strip("/-").casefold() in folded]
    return terms[:1] or [" ".join(clean(value).split()[:3])]
def make(cid,q,intent,path,section,required,forbidden,source,kind="generated"):
    return {"id":cid,"question":q,"intent":intent,"expected_relative_path":path,"expected_section":section,
      "required_terms":required,"forbidden_terms":forbidden,"source_excerpt":re.sub(r"\s+"," ",source)[:420],"case_kind":kind}

def build():
    inventory=[]; cases=[]
    for n,path in enumerate(sorted(GUIDES.rglob("*.md")),1):
        text=path.read_text(encoding="utf-8"); tm=TITLE.search(text); sm=SOURCE.search(text); sec=sections(text)
        if not tm or not sm: raise RuntimeError("Missing title/source: "+str(path))
        name=tm.group(1).strip(); rel=path.relative_to(ROOT/"knowledge_base").as_posix()
        usable=[s for s,v in sec.items() if s not in {"Kaynak bilgisi","Uyarılar"} and v]
        inventory.append({"title":name,"relative_path":rel,"category":path.relative_to(GUIDES).parts[0],
          "available_sections":list(sec),"source_url":sm.group(1),"usable_evidence_sections":usable})
        p=f"g{n:02d}"; own=[]
        if "Menü yolu" in sec:
            own.append(make(p+"-nav",name+" için kaynakta verilen menü yolu nedir?","navigation",rel,"Menü yolu",menu_terms(sec["Menü yolu"],name),[],sec["Menü yolu"]))
        if "Kullanım adımları" in sec:
            terms=procedure_labels(sec["Kullanım adımları"]); required=list(dict.fromkeys((terms[:2]+terms[-1:]) if terms else [name]))
            own.append(make(p+"-procedure",name+" nasıl yapılandırılır?","procedure",rel,"Kullanım adımları",required,[],sec["Kullanım adımları"]))
        if "Alanlar" in sec: own.append(make(p+"-fields",name+" ekranında hangi alanlar bulunur?","field_listing",rel,"Alanlar",[x for x in labels(sec["Alanlar"]) if x!="#"][:3],[],sec["Alanlar"]))
        aux="Görünür kontroller" if "Görünür kontroller" in sec else ("Alanlar" if "Alanlar" in sec else "Kapsam"); auxlabels=labels(sec.get(aux,""))
        while len(own)<2:
            if auxlabels:
                label=auxlabels[min(len(own),len(auxlabels)-1)]; intent="control_purpose" if aux=="Görünür kontroller" else "field_purpose"
                suffix=" kontrolü" if intent=="control_purpose" else ""
                own.append(make(p+"-purpose-"+str(len(own)+1),name+" ekranında "+label+suffix+" ne işe yarar?",intent,rel,aux,[label],[],sec[aux]))
            else:
                question=(name+" nedir?") if not own else (name+" hakkında kaynak ne açıklıyor?")
                own.append(make(p+"-scope-"+str(len(own)+1),question,"general_information",rel,"Kapsam",scope_terms(name,sec.get("Kapsam","")),[],sec.get("Kapsam","")))
        cases.extend(own[:2])
    seen={x["question"] for x in cases}
    for cid,q,intent,path,section,required,forbidden in CRITICAL:
        if q not in seen:
            source=sections((ROOT/"knowledge_base"/path).read_text(encoding="utf-8")).get(section,"")
            cases.append(make(cid,q,intent,path,section,required,forbidden,source,"critical_regression"))
    data={"schema_version":1,"generated_without_llm":True,"guide_count":len(inventory),"question_count":len(cases),
      "inventory":inventory,"cases":cases,"source_incomplete_guides":[x["relative_path"] for x in inventory if x["usable_evidence_sections"]==["Kapsam"]]}
    DATASET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return data

def chunk(x): return {"document_name":x.document_name,"relative_path":x.relative_path,"section_title":x.section_title,
 "chunk_index":x.chunk_index,"similarity_score":round(x.similarity_score,6),"chunk_text":x.chunk_text}
class Trace:
    def __init__(self,service):
        self.initial=[]; self.reranked=[]; search0=service._retriever.retrieve_with_embedding; rank0=service._reranker.rank
        async def search(embedding,top_k):
            result=await search0(embedding,top_k); self.initial=result; return result
        def rank(question,candidates,intent):
            result=rank0(question,candidates,intent); self.reranked=result; return result
        service._retriever.retrieve_with_embedding=search; service._reranker.rank=rank
    def reset(self): self.initial=[]; self.reranked=[]

def evaluate(test,response,trace,duration):
    answer=response.response; folded=answer.casefold(); expected=test["expected_relative_path"]; citations=[x.model_dump() for x in response.sources]
    paths=[x["relative_path"] for x in citations]
    allowed_paths={expected}
    if test["intent"]=="comparison": allowed_paths.add("guides/antikor_v2/vpn/ssl-vpn-ayarlari.md")
    source_ok=allowed_paths.issubset(set(paths))
    section_ok=any(x["relative_path"]==expected and x["section_title"]==test["expected_section"] for x in citations)
    missing=[x for x in test["required_terms"] if x.casefold() not in folded]; forbidden=[x for x in test["forbidden_terms"] if x.casefold() in folded]
    limitation=bool(test["required_terms"]) and any(x in folded for x in LIMITS); unrelated=bool(forbidden) or any(x.startswith("guides/antikor_v2/") and x not in allowed_paths for x in paths)
    source_text=(ROOT/"knowledge_base"/expected).read_text(encoding="utf-8").casefold()
    unknown=[x for x in ANSWER_LABEL.findall(answer) if x.casefold() not in source_text]
    detected=IntentClassifier.classify(test["question"]).value; intent_ok=detected==test["intent"]
    cursor=-1; order_ok=True
    if test["intent"]=="procedure":
        for term in test["required_terms"]:
            position=folded.find(term.casefold(),cursor+1)
            if position<0: order_ok=False; break
            cursor=position
    passed=source_ok and section_ok and not missing and not forbidden and not limitation and not unknown and not unrelated and intent_ok and order_ok
    if not source_ok: cause,fix="A. Retrieval failure","retrieval review"
    elif not section_ok: cause,fix="B. Wrong section selection","section-selection review"
    elif missing or limitation or unknown or unrelated or not order_ok: cause,fix="C. LLM answer failure","answer-generation review"
    elif not intent_ok: cause,fix="E. Ambiguous generated test question","validation-question review"
    else: cause=fix=None
    checks={"source_correct":source_ok,"section_correct":section_ok,"intent_correct":intent_ok,"required_terms_missing":missing,
      "forbidden_terms_found":forbidden,"false_limitation":limitation,"unsupported_claim":bool(unknown),"unknown_ui_labels":unknown,
      "unrelated_topic":unrelated,"procedure_order_correct":order_ok,"citation_correct":source_ok}
    return {**test,"detected_intent":detected,"initial_semantic_candidates":[chunk(x) for x in trace.initial],
      "reranked_candidates":[{**chunk(x.chunk),"semantic_rank":x.semantic_rank,"rerank_score":round(x.rerank_score,6),"lexical_support":round(x.lexical_support,6)} for x in trace.reranked],
      "selected_document":paths[0] if paths else None,"selected_sections":[x["section_title"] for x in citations],"generated_answer":answer,
      "returned_citations":citations,"response_duration_seconds":round(duration,3),"checks":checks,"passed":passed,
      "root_cause_classification":cause,"recommended_fix_type":fix}

def summarize(data,results,runtime):
    generated=[x for x in results if x["case_kind"]=="generated"]; grouped=defaultdict(list)
    for x in generated: grouped[x["expected_relative_path"]].append(x)
    good=[p for p,v in grouped.items() if all(x["passed"] for x in v)]; bad=[p for p,v in grouped.items() if not all(x["passed"] for x in v)]
    passed=sum(x["passed"] for x in results); wrong=sum(not x["checks"]["source_correct"] for x in results); drift=sum(x["checks"]["unrelated_topic"] for x in results); unsupported=sum(x["checks"]["unsupported_claim"] for x in results)
    result={"total_guides":data["guide_count"],"total_questions":len(results),"generated_guide_questions":len(generated),"critical_regression_questions":len(results)-len(generated),
      "passed_questions":passed,"failed_questions":len(results)-passed,"pass_rate":round(100*passed/max(len(results),1),2),
      "fully_validated_guide_count":len(good),"guide_level_pass_rate":round(100*len(good)/max(data["guide_count"],1),2),"failed_guides":bad,
      "source_content_review_guides":data["source_incomplete_guides"],"retrieval_review_guides":sorted({x["expected_relative_path"] for x in results if x["root_cause_classification"] in {"A. Retrieval failure","B. Wrong section selection"}}),
      "failure_categories":dict(Counter(x["root_cause_classification"] for x in results if not x["passed"])),"wrong_source_count":wrong,
      "wrong_section_count":sum(not x["checks"]["section_correct"] for x in results),"false_limitation_count":sum(x["checks"]["false_limitation"] for x in results),
      "unsupported_claim_count":unsupported,"unrelated_topic_count":drift,"citation_error_count":sum(not x["checks"]["citation_correct"] for x in results),
      "average_response_duration_seconds":round(sum(x["response_duration_seconds"] for x in results)/max(len(results),1),3),"runtime":runtime}
    result["ready_for_remaining_extraction"]=bool(data["guide_count"]==42 and len(grouped)==42 and result["pass_rate"]>=95 and wrong==0 and unsupported==0 and drift==0)
    return result

def write_reports(summary,results):
    (OUT/"validation_summary.md").write_text("\n".join(["# Sprint 21 Validation Summary","",*[f"- {k}: {v}" for k,v in summary.items() if k!="runtime"]]),encoding="utf-8")
    lines=["# Failed Cases",""]
    for x in results:
        if x["passed"]: continue
        lines += ["## "+x["id"]+": "+x["question"],"","- Expected source: "+x["expected_relative_path"],"- Actual source: "+str(x["selected_document"]),
          "- Expected section: "+x["expected_section"],"- Actual sections: "+", ".join(x["selected_sections"]),"- Root cause: "+str(x["root_cause_classification"]),
          "- Recommended fix: "+str(x["recommended_fix_type"]),"",x["generated_answer"],""]
    failure_name="remaining_failures.md" if SPRINT=="sprint22" else "failed_cases.md"
    (OUT/failure_name).write_text("\n".join(lines),encoding="utf-8")

async def run(data,limit=None):
    s=get_settings(); llm=OllamaProvider(s.ollama_host,s.chat_model,s.request_timeout,s.chat_max_tokens); emb=OllamaEmbeddingProvider(s.ollama_host,s.embedding_model,s.request_timeout)
    await llm.start(); await emb.start(); vector=ChromaVectorStoreProvider(s.vector_db_path,s.vector_collection_name)
    retrieval=RetrievalService(EmbeddingService(emb),vector,s.retrieval_candidate_k,s.chat_context_max_chunks,s.retrieval_min_similarity)
    trace=Trace(retrieval); chat=ChatService(llm,PromptBuilder.from_defaults(),retrieval,s.retrieval_min_similarity); OUT.mkdir(parents=True,exist_ok=True)
    selected=data["cases"][:limit] if limit else data["cases"]; completed={}
    if REPORT.exists():
        try: completed={x["id"]:x for x in json.loads(REPORT.read_text(encoding="utf-8")).get("results",[])}
        except (OSError,ValueError): pass
    started=perf_counter()
    try:
        for n,test in enumerate(selected,1):
            if test["id"] in completed: print(f"[{n}/{len(selected)}] RESUME {test['id']}",flush=True); continue
            trace.reset(); tick=perf_counter()
            try: result=evaluate(test,await chat.generate_response(test["question"]),trace,perf_counter()-tick)
            except Exception as exc:
                checks={"source_correct":False,"section_correct":False,"intent_correct":False,"required_terms_missing":test["required_terms"],"forbidden_terms_found":[],"false_limitation":False,"unsupported_claim":False,"unknown_ui_labels":[],"unrelated_topic":False,"procedure_order_correct":False,"citation_correct":False}
                result={**test,"detected_intent":IntentClassifier.classify(test["question"]).value,"initial_semantic_candidates":[chunk(x) for x in trace.initial],"reranked_candidates":[],"selected_document":None,"selected_sections":[],"generated_answer":"","returned_citations":[],"response_duration_seconds":round(perf_counter()-tick,3),"checks":checks,"passed":False,"root_cause_classification":"C. LLM answer failure","recommended_fix_type":"runtime review","error":type(exc).__name__+": "+str(exc)}
            completed[test["id"]]=result; ordered=[completed[x["id"]] for x in selected if x["id"] in completed]
            runtime={"chat_model":s.chat_model,"embedding_model":s.embedding_model,"vector_collection_name":s.vector_collection_name,"vector_db_path":str(s.vector_db_path),"candidate_k":s.retrieval_candidate_k,"context_max_chunks":s.chat_context_max_chunks,"elapsed_seconds":round(perf_counter()-started,3)}
            summary=summarize(data,ordered,runtime); REPORT.write_text(json.dumps({"summary":summary,"inventory":data["inventory"],"results":ordered},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print(f"[{n}/{len(selected)}] {test['id']} {'PASS' if result['passed'] else 'FAIL'} {result['response_duration_seconds']}s",flush=True)
    finally: await emb.close(); await llm.close()
    ordered=[completed[x["id"]] for x in selected if x["id"] in completed]; runtime={"chat_model":s.chat_model,"embedding_model":s.embedding_model,"vector_collection_name":s.vector_collection_name,"vector_db_path":str(s.vector_db_path),"candidate_k":s.retrieval_candidate_k,"context_max_chunks":s.chat_context_max_chunks,"elapsed_seconds":round(perf_counter()-started,3)}
    summary=summarize(data,ordered,runtime); REPORT.write_text(json.dumps({"summary":summary,"inventory":data["inventory"],"results":ordered},ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); write_reports(summary,ordered); print(json.dumps(summary,ensure_ascii=False),flush=True)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--dataset-only",action="store_true"); p.add_argument("--limit",type=int); a=p.parse_args()
    data=build(); print(f"dataset guides={data['guide_count']} questions={data['question_count']}",flush=True)
    if not a.dataset_only: asyncio.run(run(data,a.limit))
if __name__=="__main__": main()
