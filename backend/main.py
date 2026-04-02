from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from typing import List, Optional
import uuid
from datetime import datetime

from core.document_processor import DocumentProcessor
from core.llm_analyzer import LLMAnalyzer
from database.models import Analysis, AnalysisResult
from database.database import get_db, SessionLocal
from schemas.analysis import AnalysisRequest, AnalysisResponse

load_dotenv()

app = FastAPI(
    title="AWS DATG Analyzer API",
    description="API pour analyser les documents d'architecture AWS",
    version="1.0.0"
)

# CORS configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
document_processor = DocumentProcessor()
llm_analyzer = LLMAnalyzer()

@app.get("/")
async def root():
    return {"message": "AWS DATG Analyzer API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    llm_provider: str = "openai",
    llm_model: Optional[str] = None,
    include_aws_validation: bool = False
):
    """
    Analyse un document DATG et évalue la conformité aux bonnes pratiques AWS.
    """
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.txt', '.md']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non supporté. Types autorisés: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Process document
        processed_doc = document_processor.process(content, file_extension)
        
        # Analyze with LLM
        analysis_result = llm_analyzer.analyze(
            document_text=processed_doc.text,
            llm_provider=llm_provider,
            llm_model=llm_model,
            include_aws_validation=include_aws_validation
        )
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        
        # Save to database (optional)
        db = SessionLocal()
        try:
            analysis = Analysis(
                id=analysis_id,
                filename=file.filename,
                file_size=len(content),
                llm_provider=llm_provider,
                llm_model=llm_model or llm_analyzer.get_default_model(llm_provider),
                include_aws_validation=include_aws_validation,
                created_at=datetime.utcnow()
            )
            
            result = AnalysisResult(
                analysis_id=analysis_id,
                overall_score=analysis_result.overall_score,
                security_score=analysis_result.security_score,
                reliability_score=analysis_result.reliability_score,
                performance_score=analysis_result.performance_score,
                cost_optimization_score=analysis_result.cost_optimization_score,
                operational_excellence_score=analysis_result.operational_excellence_score,
                risks=analysis_result.risks,
                recommendations=analysis_result.recommendations,
                raw_response=analysis_result.raw_response
            )
            
            db.add(analysis)
            db.add(result)
            db.commit()
        except Exception as db_error:
            db.rollback()
            # Continue even if DB fails
            print(f"Database error (analysis saved locally): {db_error}")
        finally:
            db.close()
        
        # Prepare response
        response = AnalysisResponse(
            analysis_id=analysis_id,
            filename=file.filename,
            timestamp=datetime.utcnow().isoformat(),
            **analysis_result.dict()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

@app.get("/analyses")
async def list_analyses(limit: int = 10, offset: int = 0):
    """
    Liste les analyses précédentes.
    """
    db = SessionLocal()
    try:
        analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).offset(offset).limit(limit).all()
        return [
            {
                "id": a.id,
                "filename": a.filename,
                "created_at": a.created_at.isoformat(),
                "llm_provider": a.llm_provider,
                "llm_model": a.llm_model
            }
            for a in analyses
        ]
    finally:
        db.close()

@app.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Récupère les détails d'une analyse spécifique.
    """
    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        result = db.query(AnalysisResult).filter(AnalysisResult.analysis_id == analysis_id).first()
        
        return {
            "analysis": {
                "id": analysis.id,
                "filename": analysis.filename,
                "file_size": analysis.file_size,
                "llm_provider": analysis.llm_provider,
                "llm_model": analysis.llm_model,
                "include_aws_validation": analysis.include_aws_validation,
                "created_at": analysis.created_at.isoformat()
            },
            "result": {
                "overall_score": result.overall_score,
                "security_score": result.security_score,
                "reliability_score": result.reliability_score,
                "performance_score": result.performance_score,
                "cost_optimization_score": result.cost_optimization_score,
                "operational_excellence_score": result.operational_excellence_score,
                "risks": result.risks,
                "recommendations": result.recommendations
            } if result else None
        }
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)