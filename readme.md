## Project Overview

This project implements a **Delhi Metro Route and Schedule Simulator** using only **core Python**  
(*no external libraries such as pandas, numpy, or pickle*).

It provides the following major components:

---

## 1. Metro Timings Module
- Finds the **next metro arrival time** at a given station from both directions.
- Uses **peak/off-peak frequencies**.
- Uses **station-to-station travel times** from the `.txt` dataset.

---

## 2. Journey Planner
- Computes the **best route** between any two stations.
- Supports **direct routes** and **single interchange** routes.
- Computes **arrival times** at each station.
- Shows **next available trains** during transfers.
- Calculates **total travel time** and **total distance**.
- Computes **fare** based on **distance slabs**.
- Displays **station layout**  
  *(Elevated / Underground / At-grade)*.
- Displays **parking availability**.
- Handles **out-of-service hours** gracefully.


### 3. True Schedule-Aware Journey Planner (Peak + Off-Peak Calculation)

I implemented a **complete time-aware journey estimation** that considers:

- **Peak hours** (8–10 AM, 5–7 PM) → 4 min frequency  
- **Off-peak hours** → 8 min frequency  
- **First & last metro service timings**  
- **Boarding dwell time** at stations  
- **Interchange walking time**  
- **Direction-based frequency lookup** (Up/Down line)  

This results in **accurate arrival time predictions** across entire routes.

### 4. Real Interchange Handling (First-leg + Second-leg Train Computation)

Instead of approximate timing, the program computes:

- **Next train on Line A**  
- **Travel time to interchange**  
- **Waiting time at interchange**  
- **Next train on Line B**  
- **Final arrival time**  

This matches **real metro behavior** and as the assignment’s expected “add fixed time + interchange”.

### 5. Automatic Route Path Generation 
  
I designed a **custom path solver**:

- Checks if **source & destination lie on the same line** → Direct route  
- Searches for **single-transfer routes** via:  
  - Shared stations  
  - Interchange metadata  
  - Line name cross-links  
- Builds **combined route path**  
- Computes **travel offset** using preprocessed cumulative distances  

This respects assignment constraints while still supporting **city-wide routing**.

### 6. Service Hours Enforcement (User Warning)

If the user enters time outside **06:00 AM – 11:00 PM**:

- The program **warns the user**, showing the valid service hours  
- **No journey** is planned until a valid time is entered  

This prevents **unrealistic outputs**.


---

## Data Included

### Metro Network Data

The metro network data used in this project was **manually compiled** using publicly available information from the **Delhi Metro Rail Corporation (DMRC) official website**, including:

- Route maps  
- Station lists  
- Interchange stations  
- Station facilities  

Additional reference material, such as travel times, line structures, and station order, was verified using:

- Delhi Metro mobile app  
- Official PDF route diagrams  
- Publicly accessible transit resources (e.g., route maps published by DMRC)  

> **Note:** External datasets or APIs were **not allowed** as per assignment guidelines.  
> The extracted information was **cleaned, formatted, and stored manually** in a structured text file (`metro_data.txt`) for use by the simulator.


## Data Structure

The data begins with a clear block for each line, for example:
```python
[BLUE LINE - MAIN]
Info: Start_Point=Dwarka Sector 21
Info: End_Point=Noida Electronic City
Info: First_Train=06:00
Info: Last_Train=23:00
```

This structure clearly separates:

- **Line-level information**  
- **Station-level information**

This approach avoids confusion and allows the program to quickly extract **line start/end points**, **timings**, and **basic attributes**.

###  Minimizes Parsing Complexity

Since external libraries (**pandas, numpy, JSON, pickle**) are not allowed, the data must be parsed using:

- `read()`  
- `split()`  
- `strip()`  
- loops

The chosen format:
```python
Format: Station Name | Approx Time to Next | Interchange | Layout | Parking | Distance(km)
```

is very easy to split using:

```python
parts = line.split("|")
```
This makes parsing simple and less error-prone.




For each station:
- **Station Name**  
- **Approx. time to next station**  
- **Interchange tokens** (Line names / Station names)  
- **Station Layout** (Elevated / Underground / At-grade)  
- **Parking availability** (Available / -)  
- **Distance from starting station** (in km)  

> Multiple lines are grouped using `END`.

---

The dataset currently includes **7 route sections** covering **6 major lines**:

- **Blue Line (Main):** Dwarka Sec 21 ↔ Noida Electronic City  
- **Blue Line (Branch):** Yamuna Bank ↔ Vaishali  
- **Magenta Line:** Krishna Park Extn ↔ Botanical Garden  
- **Yellow Line:** Samaypur Badli ↔ Millennium City Centre  
- **Red Line:** Rithala ↔ Shaheed Sthal  
- **Violet Line:** Kashmere Gate ↔ Raja Nahar Singh  
- **Pink Line:** Majlis Park ↔ Shiv Vihar

### Advantages of the Structured Text Format

This structured text format is the **best choice** because:

- It is **human-readable**.  
- Easy to **parse with basic Python file I/O**.  
- Supports both **timing** and **journey-planning** features.  
- Can be **extended or modified** without changing program logic.  

The clear separation between **line metadata** and **station records** ensures:

- **Efficient processing**  
- **Accurate simulation**  

This makes it **ideal for my project** where external libraries are restricted.



# Assumptions Made

---

###### 1. Service Hours
- Metro starts at **06:00 AM**  
- Metro ends at **11:00 PM**  
- If the user enters a time outside this range:
  1. Program prints a **warning**.  
  2. No journey plan is shown.

---

###### 2. Train Frequency

| Time Period           | Frequency        |
|-----------------------|----------------|
| Peak: 08:00–10:00 AM  | Every 4 min     |
| Peak: 05:00–07:00 PM  | Every 4 min     |
| Off-Peak              | Every 8 min     |

---

###### 3. Boarding / Deboarding and Interchange Time
- `DWELL_TIME = 0.5` → 30 seconds boarding dwell  
- `INTERCHANGE_TIME = 2` → 2 minutes transfer/walking

---

###### 4. First Train at a Station
- First departure at **06:00 AM** from the line origin  
- Arrival at a station = **06:00 + offset-from-origin**

---

###### 5. Route Logic
Supports:
- Direct path on the same line  
- Single transfer using a shared station






# 📘 Instructions to Run the Delhi Metro Simulator

This program provides **two main functionalities**:

1. **Metro Timings Module** – Shows the next 6 trains in both directions from any station.  
2. **Ride Journey Planner** – Provides a complete journey plan including transfers, timings, total distance, and fare.

## Project Folder Structure
```python
project-folder/
│
├── 2023241_metro_simulator.py    # Main Python script
├── metro_data.txt                # Metro network data
└── README.md                     # README file
```

Follow the steps below to run the program:

## How to Run the Simulator

1. **Open Terminal**.

2. **Run the main script**:

```bash
python .\2023241_metro_simulator.py
```
After running the program, you will see:
```python
Select an option:
Metro Timings Module
Ride Journey Planner
Exit
Enter choice (0/1/2):
1
```


You can choose any module:

| Input | Action                     |
|-------|----------------------------|
| 1     | Metro Timings Module       |
| 2     | Ride Journey Planner       |
| 0     | Exit program               |

---

## 🕒 1. Metro Timings Module – Instructions

When you enter `1`, all available lines loaded from the file are displayed:
```python
LOADED LINES: ['BLUE LINE - MAIN', 'BLUE LINE - BRANCH', 'MAGENTA LINE', 'YELLOW LINE', 'RED LINE', 'VIOLET LINE', 'PINK LINE']
Enter Line (e.g., BLUE LINE - BRANCH, MAGENTA LINE, BLUE LINE - MAIN, RED LINE, YELLOW LINE, PINK LINE, VOILET LINE):
```

### Step 1 → Enter the Line Name
- You may enter exact or slightly misspelled names (fuzzy matching works), e.g.:

```python
voilet line
```

- Program automatically corrects it to: `VIOLET LINE`.

### Step 2 → Enter the Station Name
- Partial names are accepted, e.g.:
```python
harkesh nagar
```

### Step 3 → Enter Current Time
- Must be in 24-hour format, e.g.:

```python 
14:40 
output example
Line: VIOLET LINE
Station: Harkesh Nagar Okhla
Current time: 14:40

Trains towards Raja Nahar Singh:
  14:42, 14:50, 14:58, 15:06, 15:14, 15:22

Trains towards Kashmere Gate:
  14:41, 14:49, 14:57, 15:05, 15:13, 15:21
```

You will then be returned to the main menu.

---

## 🚆 2. Ride Journey Planner – Instructions

```python
Select an option:
Metro Timings Module
Ride Journey Planner
Exit
Enter choice (0/1/2):
2
```


### Step 1 → Source Station
- Partial names accepted, e.g.:

```python
harkesh nagar
```

### Step 2 → Destination Station
```python
botanical garden
```

### Step 3 → Time of Travel
- Must be in 24-hour format, e.g.:

```python
14:41
```

### Output Example
```python
Journey Plan:
Start at Harkesh Nagar Okhla (Violet Line), layout - Elevated, Parking - Yes
Next metro at 14:41
Arrive at Kalkaji Mandir at 14:46, layout - Underground, Parking - Yes
Transfer to Magenta Line
Next Magenta Line metro departs at 14:48, layout - Underground, Parking - Yes
Arrive at Botanical Garden at 15:06, layout - Elevated, Parking - Yes
Total distance: 12.00 km
Total travel time: 24 minutes
Fare: ₹30
```

↩ Returning to Main Menu
```python
Select an option:
Metro Timings Module
Ride Journey Planner
Exit
Enter choice (0/1/2):
0
```
After each module finishes, you will automatically return to:

Continue using the tool or press `0` to exit.


