from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from model import predict_mood_score, train_model_if_needed
from recommendations import generate_recommendations
import os

# Check if model exists, train if needed
train_model_if_needed()

app = FastAPI(title="Mood Tracker API", 
              description="API to predict mood score based on daily habits and provide recommendations")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://mental-health-app-wine.vercel.app",
                  "https://revibe-wine.vercel.app"
                  ],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class MoodInput(BaseModel):
    day_rating: str = Field(description="Text description of your day")
    water_intake: float = Field(description="Water intake in liters", ge=0)
    people_met: int = Field(description="Number of people met", ge=0)
    exercise: int = Field(description="Exercise duration in minutes", ge=0)
    sleep: float = Field(description="Sleep duration in hours", ge=0)
    screen_time: float = Field(description="Screen time in hours", ge=0)
    outdoor_time: float = Field(description="Time spent outdoors in hours", ge=0)
    stress_level: Literal["Low", "Medium", "High"] = Field(description="Stress level")
    food_quality: Literal["Healthy", "Moderate", "Unhealthy"] = Field(description="Food quality")

    # Updated validator syntax for Pydantic v2
    @field_validator('water_intake', 'sleep', 'screen_time', 'outdoor_time')
    @classmethod
    def check_reasonable_values(cls, v, info):
        max_values = {
            'water_intake': 15,
            'sleep': 24,
            'screen_time': 24,
            'outdoor_time': 24
        }
        field_name = info.field_name
        if v > max_values[field_name]:
            raise ValueError(f"{field_name} seems unreasonably high")
        return v

class Recommendation(BaseModel):
    priority: Literal["High", "Medium", "Low"]
    recommendation: str
    category: str

class MoodOutput(BaseModel):
    mood_score: float = Field(description="Predicted mood score (0-10)")
    recommendations: List[Recommendation] = Field(description="Personalized recommendations with priority levels")

@app.post("/predict", response_model=MoodOutput, summary="Predict mood score")
async def predict_mood(input_data: MoodInput):
    try:
        # Predict mood score
        mood_score = predict_mood_score(
            day_rating=input_data.day_rating,
            water_intake=input_data.water_intake,
            people_met=input_data.people_met,
            exercise=input_data.exercise,
            sleep=input_data.sleep,
            screen_time=input_data.screen_time,
            outdoor_time=input_data.outdoor_time,
            stress_level=input_data.stress_level,
            food_quality=input_data.food_quality
        )
        
        # Generate recommendations
        recommendations = generate_recommendations(
            water_intake=input_data.water_intake,
            people_met=input_data.people_met,
            exercise=input_data.exercise,
            sleep=input_data.sleep,
            screen_time=input_data.screen_time,
            outdoor_time=input_data.outdoor_time,
            stress_level=input_data.stress_level,
            food_quality=input_data.food_quality
        )
        
        return MoodOutput(mood_score=round(mood_score, 1), recommendations=recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Bind to 0.0.0.0 to be accessible from outside the container
    uvicorn.run(app, host="0.0.0.0", port=port)
