# Bonus Part

## 1. Fare calculation

Fares in this project are calculated based on the total distance travelled between the source and destination stations.

The program reads **per-segment distances** (distance from one station to the next) from the metro data file and **sums those distances** for the segments actually traveled by the passenger.

The resulting **total distance (in km)** is then **mapped to a fare slab**, which determines the fixed fare for the corresponding distance range.


## Calculation Steps (Algorithm)

### 1. Parse Distances from File
Each station row in `metro_data.txt` contains a **Distance (km)** field representing the distance from that station to the next station on the same line.  
The parser reads and stores this distance value in the station record.

### 2. Identify Route Segments

#### **Direct Route (Same Line)**
- The program finds the indices of the source and destination stations on the same line.
- It sums the **per-segment distance values** between those indices.

#### **Route with One Transfer**
If a transfer is required, the program:
- Sums distances from **source → transfer station** on Line A.
- Sums distances from **transfer → destination** on Line B.
- Adds the two segment distances to get the full route distance.

### 3. Compute Total Distance
The sum of all per-segment distances gives the **total distance (in km)**.  
The value is handled as a floating-point number and printed with **two decimal places**.

### 4. Map Total Distance to Fare Slab
The program applies a **tiered fare slab** to convert total distance into a monetary fare.  
(Refer to the fare slab table above.)

### 5. Print Results
The journey output includes:
- `Total distance: X.XX km`
- `Fare: ₹Y`


## Implementation Notes (Where to Look in the Code)

### Parsing Distances
- The parser reads **6 columns** per station entry.
- The last field is stored as `station['distance']`.
- Implemented in `parse_metro_file()` in the main script.
- This function loads the **Distance(km)** field into each station record.

### Distance Summation
- The function  
  `compute_distance_on_line(lines_data, line_name, start_station, end_station)`  
  calculates the **total distance (km)** between two stations on the same line.
- It sums the per-segment distances stored in each station record.

### Fare Mapping
- The function `fare_by_distance_km(dist_km)` implements the **fare slab mapping** defined earlier.
- It converts total distance → fare amount.

### Output
The planner prints the results in the following format:
Total distance: {dist:.2f} km
Fare: ₹{fare}

## Function Signatures Used in the Project

```python
dist_km = compute_distance_on_line(lines_data, line_used, src, best_path[-1])
fare    = fare_by_distance_km(dist_km)
```


## Fare Slab Used (Default in the Project)

The default slab mapping implemented in `fare_by_distance_km()`:

| Distance Range         | Fare (₹) |
|------------------------|----------|
| 0.00 km – 2.00 km      | 10       |
| >2.00 km – 5.00 km     | 20       |
| >5.00 km – 12.00 km    | 30       |
| >12.00 km – 21.00 km   | 40       |
| >21.00 km – 32.00 km   | 50       |
| >32.00 km              | 60       |



## 2. Addition of Four New Metro Lines (Dataset Update)

To make the simulator more complete and realistic, four additional Delhi Metro lines were manually added to the dataset located at:

`metro_data.txt`

These new lines expand network coverage, increase interchange possibilities, and improve the accuracy of the route planner.

### Newly Added Lines
- **Pink Line**
- **Red Line**
- **Violet Line**
- **Yellow Line**  


### Data Format
Each added line follows the same structure as the existing lines in the dataset:

`Format: Station Name | Approx Time to Next | Interchange | Layout | Parking | Distance(km)`

## 3. Station Metadata Display

Each station report includes:

- **Layout:** Elevated / Underground / At-grade  
- **Parking:** Yes / No  
- **Line Name:** formatted display  

This makes the **journey output informative** and **visually structured**.

## 4. Intelligent Line Name Matching (Typo Correction + Fuzzy Search)

The assignment expected basic string matching.  
I implemented a **robust multi-level matching algorithm**:

- **Exact case-insensitive match**  
- **Substring & “starts-with” match**  
- **Fuzzy match** using Levenshtein distance  
- **Normalization** to ignore punctuation & extra spaces  

This allows the program to correctly interpret user inputs like:

- `"voilet line"` → `Violet Line`  
- `"blu line - main"` → `Blue Line - Main`  
- `"pinkln"` → `Pink Line`  

This significantly improves **user experience** and **tolerance for typing errors**.

## 5. Robust Input Fallbacks & Auto-Corrections

- **Station prefix matching** (e.g., `"dwar"` → `Dwarka`)  
- **Case-insensitive input**  
- **Whitespace-tolerant matching**  
- **Auto-correct suggestions**  
- **Safe fallback** for invalid or ambiguous inputs



