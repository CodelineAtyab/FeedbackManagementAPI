from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID, uuid4
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Feedback Management API",
    description="A RESTful API for managing user feedback with CRUD operations",
    version="1.0.0"
)

# In-memory storage for feedbacks
feedbacks_db = {}

# Initialize with dummy data
def initialize_dummy_data():
    """Initialize the database with 10 dummy feedback records"""
    dummy_feedbacks = [
        {"feedback_content": "Excellent service! Very satisfied with the product quality.", "email_address": "john.doe@example.com"},
        {"feedback_content": "Fast delivery and great customer support. Highly recommend!", "email_address": "sarah.smith@example.com"},
        {"feedback_content": "The product met my expectations. Good value for money.", "email_address": "mike.johnson@example.com"},
        {"feedback_content": "Outstanding experience! Will definitely order again.", "email_address": "emily.brown@example.com"},
        {"feedback_content": "Good quality but shipping took longer than expected.", "email_address": "david.wilson@example.com"},
        {"feedback_content": "Amazing customer service team. They resolved my issue quickly.", "email_address": "lisa.garcia@example.com"},
        {"feedback_content": "Product works as described. Very happy with my purchase.", "email_address": "robert.martinez@example.com"},
        {"feedback_content": "Great experience overall. The website is easy to navigate.", "email_address": "jennifer.davis@example.com"},
        {"feedback_content": "Impressed with the quality and attention to detail.", "email_address": "william.rodriguez@example.com"},
        {"feedback_content": "Fantastic product! Exceeded my expectations in every way.", "email_address": "amanda.miller@example.com"}
    ]
    
    for dummy in dummy_feedbacks:
        feedback_uuid = uuid4()
        feedback = Feedback(
            uuid=feedback_uuid,
            feedback_content=dummy["feedback_content"],
            email_address=dummy["email_address"]
        )
        feedbacks_db[feedback_uuid] = feedback

# Pydantic models
class FeedbackBase(BaseModel):
    """Base model for feedback data"""
    feedback_content: str = Field(..., min_length=1, max_length=1000, description="The content of the feedback")
    email_address: EmailStr = Field(..., description="Email address of the person providing feedback")

class FeedbackCreate(FeedbackBase):
    """Model for creating new feedback"""
    pass

class FeedbackUpdate(BaseModel):
    """Model for updating existing feedback"""
    feedback_content: Optional[str] = Field(None, min_length=1, max_length=1000, description="The content of the feedback")
    email_address: Optional[EmailStr] = Field(None, description="Email address of the person providing feedback")

class Feedback(FeedbackBase):
    """Model for feedback response with UUID"""
    uuid: UUID = Field(..., description="Unique identifier for the feedback")

    class Config:
        json_schema_extra = {
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "feedback_content": "Great service!",
                "email_address": "user@example.com"
            }
        }

# Initialize dummy data on startup
initialize_dummy_data()

# CRUD Endpoints
@app.post(
    "/feedbacks",
    response_model=Feedback,
    status_code=status.HTTP_201_CREATED,
    summary="Create new feedback",
    description="Create a new feedback entry with content and email address. Returns the created feedback with a unique UUID.",
    tags=["Feedbacks"]
)
async def create_feedback(feedback: FeedbackCreate):
    """
    Create a new feedback entry.
    
    - **feedback_content**: The feedback message (required, 1-1000 characters)
    - **email_address**: Valid email address of the user (required)
    
    Returns the created feedback with a unique UUID.
    """
    feedback_uuid = uuid4()
    new_feedback = Feedback(
        uuid=feedback_uuid,
        feedback_content=feedback.feedback_content,
        email_address=feedback.email_address
    )
    feedbacks_db[feedback_uuid] = new_feedback
    return new_feedback

@app.get(
    "/feedbacks",
    response_model=List[Feedback],
    summary="Get all feedbacks",
    description="Retrieve a list of all feedback entries in the system.",
    tags=["Feedbacks"]
)
async def get_all_feedbacks():
    """
    Retrieve all feedback entries.
    
    Returns a list of all feedbacks currently stored in the system.
    """
    return list(feedbacks_db.values())

@app.get(
    "/feedbacks/{feedback_uuid}",
    response_model=Feedback,
    summary="Get feedback by UUID",
    description="Retrieve a specific feedback entry by its unique identifier (UUID).",
    tags=["Feedbacks"]
)
async def get_feedback(feedback_uuid: UUID):
    """
    Retrieve a specific feedback by UUID.
    
    - **feedback_uuid**: The unique identifier of the feedback
    
    Returns the feedback if found, otherwise raises a 404 error.
    """
    if feedback_uuid not in feedbacks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with UUID {feedback_uuid} not found"
        )
    return feedbacks_db[feedback_uuid]

@app.put(
    "/feedbacks/{feedback_uuid}",
    response_model=Feedback,
    summary="Update feedback",
    description="Update an existing feedback entry. You can update either the content, email, or both.",
    tags=["Feedbacks"]
)
async def update_feedback(feedback_uuid: UUID, feedback_update: FeedbackUpdate):
    """
    Update an existing feedback entry.
    
    - **feedback_uuid**: The unique identifier of the feedback to update
    - **feedback_content**: New feedback content (optional)
    - **email_address**: New email address (optional)
    
    Returns the updated feedback. At least one field must be provided.
    """
    if feedback_uuid not in feedbacks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with UUID {feedback_uuid} not found"
        )
    
    stored_feedback = feedbacks_db[feedback_uuid]
    update_data = feedback_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update"
        )
    
    updated_feedback = stored_feedback.model_copy(update=update_data)
    feedbacks_db[feedback_uuid] = updated_feedback
    return updated_feedback

@app.delete(
    "/feedbacks/{feedback_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete feedback",
    description="Delete a specific feedback entry by its UUID.",
    tags=["Feedbacks"]
)
async def delete_feedback(feedback_uuid: UUID):
    """
    Delete a feedback entry.
    
    - **feedback_uuid**: The unique identifier of the feedback to delete
    
    Returns no content on successful deletion. Raises 404 if feedback not found.
    """
    if feedback_uuid not in feedbacks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with UUID {feedback_uuid} not found"
        )
    del feedbacks_db[feedback_uuid]
    return None

@app.get(
    "/",
    summary="Root endpoint",
    description="Welcome message and API information",
    tags=["General"]
)
async def root():
    """Root endpoint returning API information"""
    return {
        "message": "Welcome to Feedback Management API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Run with uvicorn
if __name__ == "__main__":
    uvicorn.run("main_app:app", host="0.0.0.0", port=8000, reload=True)
