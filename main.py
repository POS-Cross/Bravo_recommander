from typing import Optional
import pandas as pd
from fastapi import FastAPI, HTTPException
import pickle

description = """
Basket Analysis is an unserpvised machine learning API that helps find rules
 asscosiation in your point of sales transactions. 🚀

## Offers

You can **generate rules** using many options.


* **Ramdan Offers** (implemented_). http://127.0.0.1:8000/rules/ramadan
* **Back To School Offers** (implemented_). http://127.0.0.1:8000/rules/school

"""

app = FastAPI(
    title="Basket Analysis API",
    description=description,
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Bravo Team",
        "url": "https://github.com/POS-Cross",
        "email": "help@bteam.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)



@app.get("/")
@app.get("/home")
def read_root():
    return {"Hello": "The system is healthy"}


@app.get("/rules/{option}")
def generate_association(option: str):
    print(option)
    match option:
        case "school":
            loaded_model = pickle.load(open('models/school_rules.pkl', 'rb'))
        case "ramadan":
            loaded_model = pickle.load(open('models/ramdan_rules.pkl', 'rb'))
        case _:
            raise HTTPException(status_code=404, detail="Option not found")

    return loaded_model.to_dict()


