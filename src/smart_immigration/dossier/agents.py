"""Points d'entrée Dossier pour un orchestrateur utilisant AgentResult."""
from ..schemas import AgentResult
from .documents import MAX_BYTES, DocumentType, extract_fields
from .routes import DossierRequest, get_dossier_report


def read_document(task_id: str, content: bytes, kind: DocumentType, media_type: str) -> AgentResult:
    warnings = []
    if not content or len(content) > MAX_BYTES or media_type not in {"text/plain", "application/pdf"}:
        warnings.append("Fournissez un spécimen TXT ou PDF de 2 Mio maximum.")
    else:
        try:
            piece = extract_fields(content, kind, media_type)
        except ValueError as error:
            warnings.append(str(error))
        else:
            return AgentResult(task_id=task_id, agent="dossier.reader", status="needs_human",
                               data={"document": piece.model_dump(mode="json")},
                               warnings=["Vérifiez les champs extraits avant de les confirmer."])
    return AgentResult(task_id=task_id, agent="dossier.reader", status="error", warnings=warnings)


def check_dossier(task_id: str, dossier: DossierRequest) -> AgentResult:
    report = get_dossier_report(dossier)
    return AgentResult(task_id=task_id, agent="dossier.checker",
                       status="ok" if report.can_validate else "needs_human",
                       source_version=report.assessment.rule_version, data=report.model_dump(mode="json"),
                       warnings=["Le consultant examine les verdicts et décide de la suite."])
