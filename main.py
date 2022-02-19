import json
from typing import Optional
from fastapi import FastAPI, Header, HTTPException,Response
import pymongo
import random
import pickle

from starlette.middleware.cors import CORSMiddleware

description = """
Offer Recommendation  is an unserpvised machine learning API that helps find rules
 asscosiation in your point of sales transactions. 🚀

## Offers

You can **generate rules** using many options.


* **Ramdan Offers** (implemented_). http://127.0.0.1:8000/rules/ramadan
* **Back To School Offers** (implemented_). http://127.0.0.1:8000/rules/school

"""

app = FastAPI(
    title="Offer Recommendation  API",
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

origins = [
    "https://khaledanaqwa.github.io",
    "http://localhost:4200",
    "185.199.108.153:443"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def splitDay(value):
    return int(value.replace("\\", "").split()[0].split("/")[0])


def splitMonth(value):
    return int(value.replace("\\", "").split()[0].split("/")[1])


def splitYear(value):
    return int(value.replace("\\", "").split()[0].split("/")[2])


Departments = {0: 'Rejected',
               100: 'Roastery',
               101: 'Produce',
               102: 'Meat & Seafood',
               103: 'Dairy',
               104: 'Deli',
               105: 'Canned/Jarred Goods',
               106: 'Frozen Foods',
               107: 'Bakery',
               108: 'Paper Goods',
               109: 'Personal & Baby Care',
               110: 'Front End',
               111: 'Dates',
               112: 'Beverages',
               333: 'Others'}
def predict(antecedent, rules, max_results= 10):
    # get the rules for this antecedent
    preds = rules[rules['antecedents'] == antecedent]
    preds = preds['consequents']
    return preds[:max_results].reset_index(drop=True).to_list()
def getPredictionForList(list,model,max_results):
    RecommendationItems=[]
    for i in list:
        preds = predict(i, model,max_results)
        item={"ItemName":i , "RecItems":preds}
        RecommendationItems.append(item)
    return RecommendationItems
DBconn =None

async def connectDB():
    client = pymongo.MongoClient(
        "mongodb://admin:2z6WfaIaxFs1gzLN@cluster0-shard-00-00.8ryat.mongodb.net:27017,cluster0-shard-00-01.8ryat.mongodb.net:27017,cluster0-shard-00-02.8ryat.mongodb.net:27017/Bravo.BravoTrasnactions?ssl=true&replicaSet=atlas-m4yex9-shard-0&authSource=admin&retryWrites=true&w=majority")
    # set a 5-second connection timeout
    try:
        print(client.server_info())
    except Exception:
        print("Unable to connect to the server.")
    DB = client.Bravo
    return DB

async def getTransactions():
    global DBconn
    if (DBconn == None):
        DBconn = await connectDB()
    BravoTrasnactions = DBconn.BravoTrasnactions
    return BravoTrasnactions

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


@app.get('/getSalesData')
async def getSales():
    BravoTrasnactions = await getTransactions()
    agg_result = BravoTrasnactions.aggregate(
        [
            {
                '$group': {
                    '_id': '$dTicketInternalKey',
                    'date': {
                        '$first': '$Invoice_Date'
                    },
                    'total': {
                        '$first': '$Total_Net_InvoiceIncVAT'
                    }
                }
            }, {
            '$group': {
                '_id': '$date',
                'total': {
                    '$sum': '$total'
                }
            }
        }, {
            '$sort': {
                '_id': 1
            }
        }
        ]
    )

    SalesData = {'SalesSum': 0,
                 "data": [
                     {
                         "name": 'This Week',
                         "data": [0, 0, 0, 0, 0, 0, 0],
                     },
                     {
                         "name": 'Last Week',
                         "data": [0, 0, 0, 0, 0, 0, 0],
                     },
                 ],
                 "dates": ['1/9', '2/9', '3/9', '4/9', '5/9', '6/9', '7/9']};
    sum = 0
    for i in agg_result:
        # print(i)
        day = splitDay(i['_id'])
        month = splitMonth(i['_id'])
        # print(day)
        if day <= 7:
            SalesData['data'][0]['data'][day - 1] = i['total']
            SalesData['dates'][day - 1] = "{}/{}".format(day, month)
            SalesData["SalesSum"] += i['total']
        elif day > 7 and day <= 14:
            SalesData['data'][1]['data'][(day - 1) % 7] = i['total']
            SalesData["SalesSum"] += i['total']

    return SalesData


@app.get('/getOrderTimeData')
async def getOrderTimeData():
    return [0, 83513, 0]


@app.get('/getTop5Dept')
async def getTop5Dept():
    BravoTrasnactions = await getTransactions()
    agg_result = BravoTrasnactions.aggregate(
        [
            {
                '$group': {
                    '_id': '$DeptNo',
                    'counts': {
                        '$sum': 1
                    }
                }
            }, {
            '$sort': {
                'counts': -1.
            }
        }, {'$limit': 5}
        ])
    Top5DepartmentData = {
        "data": [],
        "labels": []
    };
    for i in agg_result:
        # print(i)
        Top5DepartmentData["data"].append(i["counts"])
        Top5DepartmentData["labels"].append(Departments[i["_id"]])

    return Top5DepartmentData


@app.get("/getTop5Items")
async def getTop5Items():
    BravoTrasnactions = await getTransactions()
    agg_result = BravoTrasnactions.aggregate(
        [
            {
                '$group': {
                    '_id': {
                        'dItemInternalKey': '$dItemInternalKey',
                        'ItemName': '$ItemName',
                        'DeptNo': '$DeptNo'
                    },
                    'counts': {
                        '$sum': 1
                    }
                }
            }, {
            '$sort': {
                'counts': -1
            }
        }, {'$limit': 5}
        ]
    )

    Top5Items = []
    for i in agg_result:
        item = {}
        item["name"] = i["_id"]["ItemName"]
        item["departmentname"] = Departments[i["_id"]["DeptNo"]]
        item["counts"] = i["counts"]
        item["growth"] = random.randint(-1, 1)
        Top5Items.append(item)

    return Top5Items


@app.get("/getDailyData")
async def getDailyData():
    DailyData = {'data': [0, 0, 0, 0, 0, 0, 0],
                 'dates': ['1/9', '2/9', '3/9', '4/9', '5/9', '6/9', '7/9']}
    BravoTrasnactions = await getTransactions()
    agg_result = BravoTrasnactions.aggregate(
        [
            {
                '$group': {
                    '_id': '$dTicketInternalKey',
                    'date': {
                        '$first': '$Invoice_Date'
                    }
                }
            }, {
            '$group': {
                '_id': '$date',
                'count': {
                    '$sum': 1
                }
            }
        }, {
            '$project': {
                'date': {
                    '$split': [
                        '$_id', '\\/'
                    ]
                },
                '_id': 1,
                'count': 1
            }
        }, {
            '$project': {
                'count': 1,
                'day': {
                    '$arrayElemAt': [
                        '$date', 0
                    ]
                },
                'month': {
                    '$arrayElemAt': [
                        '$date', 1
                    ]
                },
                'year': {
                    '$split': [
                        {
                            '$arrayElemAt': [
                                '$date', 2
                            ]
                        }, ' '
                    ]
                }
            }
        }, {
            '$project': {
                'day': 1,
                'month': 1,
                'count': 1,
                'year': {
                    '$arrayElemAt': [
                        '$year', 0
                    ]
                }
            }
        }, {
            '$sort': {
                'count': -1
            }
        }
        ]
    )
    for i in agg_result:
        # print(i)
        if int(i["day"]) <= 7:
            DailyData['data'][int(i["day"]) - 1] = i['count']
            DailyData['dates'][int(i["day"]) - 1] = "{}/{}".format(int(i["day"]), int(i['month']))

    return DailyData

@app.get("/getRecommendation")
async def getRecommendation(response:Response,ListItems: Optional[str] = Header(None),BundelSize: Optional[str] = Header(None),ListType: Optional[str] = Header(None)):
    loaded_model = pickle.load(open('models/UpdateRamadan_rules.pkl', 'rb'))
    print(str(ListType))
    if (ListType == "School"):
        loaded_model = pickle.load(open('models/UpdateSchool_rules.pkl', 'rb'))
    response.headers['Access-Control-Allow-Origin']='*'
    response.headers['Access-Control-Allow-Methods']='GET'
    return getPredictionForList(json.loads(ListItems),loaded_model,int(BundelSize))




