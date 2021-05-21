from fastapi import FastAPI, HTTPException
from configuration import getModel
import schemas

app = FastAPI()
modelFile = open("model.pkl", 'rb')
predictModel = getModel(modelFile).model()

@app.post("/predict'")
def predict(request:schemas.Iris):
    try:
        predictmodel = predictModel.predict([[
            request.sepal_length, 
            request.sepal_width, 
            request.petal_length, 
            request.petal_width
        ]])
        return {"Predict": str(predictmodel[0])}
    except:
        raise HTTPException(status_code=404)
