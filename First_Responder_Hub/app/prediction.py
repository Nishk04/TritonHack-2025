from sklearn.cluster import KMeans
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


data = pd.read_csv("First_Responder_Hub/app/Fire-Incident.csv", sep="\t", on_bad_lines='skip')
data.columns = data.columns.str.strip() 

print(data.columns)

origin = data["Area_of_Origin"]
extent = data["Extent_Of_Fire"]
property = data["Property_Use"]
injured = data["Civilian_Casualties"]

cause = data["Possible_Cause"]

for i in range(len(origin)):
    if origin[i].find("or") > -1 and origin[i].find("Kitchen") > -1:
        origin[i] = "Kitchen"
    if origin[i].find("or") > -1 and origin[i].find("Bedroom") > -1:
        origin[i] = "Bedroom"
    if origin[i].find("Living") > -1:
        origin[i] = "Home"
    elif origin[i].find(",") > -1:
        origin[i] = origin[i][0:origin[i].find(",")]
    elif origin[i].find(" ") > -1:
        origin[i] = origin[i][0:origin[i].find(" ")]

for i in range(len(extent)):
    if extent[i].find("Confined") > -1:
        extent[i] = "Confined"
    else:
        extent[i] = "Spread"

for i in range(len(property)):
    if property[i].find("Dwelling") > -1:
        property[i] = "Home"
    elif property[i].find(",") > -1:
        property[i] = property[i][0:property[i].find(",")]
    elif property[i].find(" ") > -1:
        property[i] = property[i][0:property[i].find(" ")]



# Encode features and labels
le_origin = LabelEncoder()
le_extent = LabelEncoder()
le_property = LabelEncoder()
le_injured = LabelEncoder()
le_cause = LabelEncoder()

X = pd.DataFrame({
    "origin": le_origin.fit_transform(origin),
    "extent": le_extent.fit_transform(extent),
    "property": le_property.fit_transform(property),
    "injured": le_injured.fit_transform(injured)
})

y = le_cause.fit_transform(cause)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

knn = KNeighborsClassifier(n_neighbors=15)
knn.fit(X_train, y_train)

accuracy = knn.score(X_test, y_test)
print(f"Accuracy: {accuracy:.2f}")

# Example: Predict cause of a new incident
# Example values: origin='Kitchen', extent='Entire Building', property='Residential'


sample = [[
    le_origin.transform(['Kitchen'])[0],
    le_extent.transform(['Confined'])[0],
    le_property.transform(['School'])[0],
    le_injured.transform(["0"])[0]
]]

sample_scaled = scaler.transform(sample)
predicted = knn.predict(sample_scaled)
print("Predicted cause:", le_cause.inverse_transform(predicted)[0])


