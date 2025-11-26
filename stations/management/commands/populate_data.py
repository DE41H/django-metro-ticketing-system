import csv
from io import StringIO
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.db.models import F
from stations.models import Station, Line 

# --- Data Definition (Copied from the provided files) ---

COLOR_MAP = {
    "Red Line": "#FF0000",
    "Yellow Line": "#FFFF00",
    "Blue Line": "#0000FF",
    "Green Line": "#008000",
    "Violet Line": "#EE82EE",
    "Pink Line": "#FF69B4",
    "Magenta Line": "#FF00FF",
    "Grey Line": "#808080",
    "Airport Express": "#FFA500",
}

STATIONS_CSV = """uid,name,neighbours
1,AIIMS,29|52
2,Adarsh Nagar,67|8
3,Akshardham,110|222
4,Anand Vihar,85|89
5,Arjan Garh,47|53
6,Arthala,114|58
7,Ashok Park Main,158|63
8,Azadpur,101|112|189|2
9,Badarpur Border,178|211
10,Badkal Mor,146|182
11,Bahadurgarh City,149|15
12,Barakhamba Road,104|166
13,Bhikaji Cama Place,181|198
14,Botanical Garden,137|143|49
15,Brigadier Hoshiyar Singh,11|92
16,Central Secretariat,152|212|73|91
17,Chandni Chowk,18|88
18,Chawri Bazar,132|17
19,Chhatarpur,160|202
20,Chirag Delhi,148|51
21,Civil Lines,218|88
22,Dabri Mor - Janakpuri South,23|71
23,Dashrath Puri,147|22
24,Delhi Aerocity,28|64
25,Delhi Cantonment,125|31
26,Delhi Gate,62|68
27,Dhansa Bus Stand,121
28,Dhaula Kuan,195|24
29,Dilli Haat - INA,1|80
30,Dilshad Garden,186|78
31,Durgabai Deshmukh South Campus,198|25
32,Dwarka,122|33|38
33,Dwarka Mor,126|32
34,Dwarka Sector 10,35|41
35,Dwarka Sector 11,34|36
36,Dwarka Sector 12,35|37
37,Dwarka Sector 13,36|38
38,Dwarka Sector 14,32|37
39,Dwarka Sector 21,223|40|64
40,Dwarka Sector 8,39|41
41,Dwarka Sector 9,34|40
42,ESI - Basaidarapur,159|167
43,East Azad Nagar,221|94
44,East Vinod Nagar - Mayur Vihar-II,210|61
45,GTB Nagar,112|220
46,Ghevra,118|207
47,Ghitorni,202|5
48,Gokulpuri,106|79
49,Golf Course,133|14
50,Govindpuri,144|83
51,Greater Kailash,128|20
52,Green Park,1|57
53,Guru Dronacharya,197|5
54,HUDA City Centre,59
55,Haiderpur Badli Mor,172|67
56,Harkesh Nagar Okhla,144|74
57,Hauz Khas,103|148|52|60
58,Hindon River,187|6
59,IFFCO Chowk,54|98
60,IIT Delhi,161|57
61,IP Extension,44
62,ITO,104|26
63,Inderlok,191|7|84
64,Indira Gandhi International Airport,24|39
65,Indraprastha,203|222
66,Jaffrabad,106|221
67,Jahangirpuri,2|55
68,Jama Masjid,26|96
69,Jamia Millia Islamia,145|201
70,Janakpuri East,208|71
71,Janakpuri West,214|22|70
72,Jangpura,76|95
73,Janpath,104|16
74,Jasola Apollo,180|56
75,Jasola Vihar Shaheen Bagh,145|82
76,Jawaharlal Nehru Stadium,72|91
77,Jhandewalan,168|87
78,Jhilmil,105|30
79,Johri Enclave,193|48
80,Jor Bagh,29|97
81,Kailash Colony,115|129
82,Kalindi Kunj,143|75
83,Kalkaji Mandir,128|129|144|50
84,Kanhaiya Nagar,63|90
85,Karkarduma,4|86|226
86,Karkarduma Court,85|94
87,Karol Bagh,165|77
88,Kashmere Gate,17|192|209|21|96
89,Kaushambi,4|216
90,Keshav Puram,130|84
91,Khan Market,16|76
92,Kirti Nagar,116|15|184
93,Kohat Enclave,130|155
94,Krishna Nagar,43|86
95,Lajpat Nagar,115|148|219|72
96,Lal Qila,68|88
97,Lok Kalyan Marg,212|80
98,MG Road,197|59
99,Madipur,150|194
100,Maharaja Surajmal Stadium,123|213
101,Majlis Park,8
102,Major Mohit Sharma Rajendra Nagar,162|196
103,Malviya Nagar,175|57
104,Mandi House,12|203|62|73
105,Mansarovar Park,185|78
106,Maujpur - Babarpur,48|66
107,Mayapuri,125|167
108,Mayur Vihar Extension,110|131
109,Mayur Vihar Pocket I,110|210
110,Mayur Vihar-I,108|109|179|3
111,Mewla Maharajpur,120|182
112,Model Town,45|8
113,Mohan Estate,180|211
114,Mohan Nagar,196|6
115,Moolchand,81|95
116,Moti Nagar,169|92
117,Mundka,118|164
118,Mundka Industrial Area,117|46
119,Munirka,161|217
120,NHPC Chowk,111|178
121,Najafgarh,122|27
122,Nangli,121|32
123,Nangloi,100|124
124,Nangloi Railway Station,123|164
125,Naraina Vihar,107|25
126,Nawada,215|33
127,Neelam Chowk Ajronda,146|177
128,Nehru Enclave,51|83
129,Nehru Place,81|83
130,Netaji Subhash Place,188|189|90|93
131,New Ashok Nagar,108|135
132,New Delhi,166|18|195
133,Noida City Centre,138|49
134,Noida Electronic City,142
135,Noida Sector 15,131|136
136,Noida Sector 16,135|137
137,Noida Sector 18,136|14
138,Noida Sector 34,133|139
139,Noida Sector 52,138|140
140,Noida Sector 59,139|141
141,Noida Sector 61,140|142
142,Noida Sector 62,134|141
143,Okhla Bird Sanctuary,14|82
144,Okhla NSIC,201|50|56|83
145,Okhla Vihar,69|75
146,Old Faridabad,10|127
147,Palam,174|23
148,Panchsheel Park,179|20|57|95
149,Pandit Shree Ram Sharma,11|206
150,Paschim Vihar East,151|99
151,Paschim Vihar West,150|154
152,Patel Chowk,16|166
153,Patel Nagar,165|184
154,Peeragarhi,151|213
155,Pitampura,171|93
156,Pratap Nagar,157|191
157,Pul Bangash,156|209
158,Punjabi Bagh,194|7
159,Punjabi Bagh West,188|42
160,Qutab Minar,175|19
161,R. K. Puram,119|60
162,Raj Bagh,102|186
163,Raja Nahar Singh,177
164,Rajdhani Park,117|124
165,Rajendra Place,153|87
166,Rajiv Chowk,12|132|152|168
167,Rajouri Garden,107|169|204|42
168,Ramakrishna Ashram Marg,166|77
169,Ramesh Nagar,116|167
170,Rithala,173
171,Rohini East,155|173
172,"Rohini Sector 18,19",176|55
173,Rohini West,170|171
174,Sadar Bazaar Cantonment,147|205
175,Saket,103|160
176,Samaypur Badli,172
177,Sant Surdas(Sihi),127|163
178,Sarai,120|9
179,Sarai Kale Khan - Nizamuddin,110|148
180,Sarita Vihar,113|74
181,Sarojini Nagar,13|199
182,Sector 28,10|111
183,Seelampur,192|221
184,Shadipur,153|92
185,Shahdara,105|221
186,Shaheed Nagar,162|30
187,Shaheed Sthal,58
188,Shakurpur,130|159
189,Shalimar Bagh,130|8
190,Shankar Vihar,205|217
191,Shastri Nagar,156|63
192,Shastri Park,183|88
193,Shiv Vihar,79
194,Shivaji Park,158|99
195,Shivaji Stadium,132|28
196,Shyam Park,102|114
197,Sikanderpur,53|98
198,Sir M. Vishweshwaraiah Moti Bagh,13|31
199,South Extension,181|219
200,Subhash Nagar,204|208
201,Sukhdev Vihar,144|69
202,Sultanpur,19|47
203,Supreme Court,104|65
204,Tagore Garden,167|200
205,Terminal 1-IGI Airport,174|190
206,Tikri Border,149|207
207,Tikri Kalan,206|46
208,Tilak Nagar,200|70
209,Tis Hazari,157|88
210,Trilokpuri Sanjay Lake,109|44
211,Tughlakabad Station,113|9
212,Udyog Bhawan,16|97
213,Udyog Nagar,100|154
214,Uttam Nagar East,215|71
215,Uttam Nagar West,126|214
216,Vaishali,89
217,Vasant Vihar,119|190
218,Vidhan Sabha,21|220
219,Vinobapuri,199|95
220,Vishwa Vidyalaya,218|45
221,Welcome,183|185|43|66
222,Yamuna Bank,3|65|224
223,Yashobhoomi Dwarka Sector - 25,39
224,Laxmi Nagar,222|225
225,Nirman Vihar,224|226
226,Preet Vihar,225|85
"""

LINES_CSV = """name,stations
Red Line,187|58|6|114|196|102|162|186|30|78|105|185|221|183|192|88|209|157|156|191|63|84|90|130|93|155|171|173|170
Yellow Line,176|172|55|67|2|8|112|45|220|218|21|88|17|18|132|166|152|16|212|97|80|29|1|52|57|103|175|160|19|202|47|5|53|197|98|59|54
Blue Line,39|40|41|34|35|36|37|38|32|33|126|215|214|71|70|208|200|204|167|169|116|92|184|153|165|87|77|168|166|12|104|203|65|222|3|110|108|131|135|136|137|14|49|133|138|139|140|141|142|134|224|225|226|85|4|89|216
Green Line,63|7|158|194|99|150|151|154|213|100|123|124|164|117|118|46|207|206|149|11|15|92
Violet Line,88|96|68|26|62|104|73|16|91|76|72|95|115|81|129|83|50|144|56|74|180|113|211|9|178|120|111|182|10|146|127|177|163
Pink Line,101|8|189|130|188|159|42|167|107|125|25|31|198|13|181|199|219|95|148|179|110|109|210|44|61|4|85|86|94|43|221|66|106|48|79|193
Magenta Line,71|22|23|147|174|205|190|217|119|161|60|57|148|20|51|128|83|144|201|69|145|75|82|143|14
Grey Line,32|122|121|27
Airport Express,132|195|28|24|64|39|223
"""

# --- Core Parsing Functions ---

def parse_stations():
    """
    Parses STATIONS_CSV. 
    Returns: stations_to_create, uid_to_name map, and neighbour map using station names (PKs).
    """
    # Maps integer UID (from CSV) to Name (the PK)
    uid_to_name = {}
    # Stores neighbor relationships using the integer UID temporarily
    name_to_raw_neighbours_uids = {}
    stations_to_create = []
    
    reader = csv.DictReader(StringIO(STATIONS_CSV))
    for row in reader:
        try:
            uid = int(row["uid"])
            name = row["name"].strip()
            
            # Neighbours are still read as UIDs temporarily
            raw_neighbours_uids = [int(n) for n in row["neighbours"].split("|") if n]
            
            uid_to_name[uid] = name
            name_to_raw_neighbours_uids[name] = raw_neighbours_uids
            
            # **Correct:** Create Station object using 'name' as the primary key.
            # No need to set pk=name as it's the default behavior for the PK field.
            stations_to_create.append(Station(name=name))
        except Exception as e:
            print(f"[Warn] Skipping malformed station row: {row} -- {e}")
            
    # Second pass: Convert UID neighbours to Name neighbours (the actual PKs)
    final_neighbour_map = {}
    for station_name, neighbour_uids in name_to_raw_neighbours_uids.items():
        # Convert list of UID integers to a list of Name strings
        neighbour_names = [uid_to_name.get(nuid) for nuid in neighbour_uids if nuid in uid_to_name]
        final_neighbour_map[station_name] = [n for n in neighbour_names if n]

    # The returned neighbour map is now keyed by Station Name and contains a list of Neighbour Names.
    return stations_to_create, uid_to_name, final_neighbour_map

def parse_lines():
    """Parses LINES_CSV and prepares data for Line creation and linking to stations."""
    lines_to_create = []
    raw_line_data = []
    reader = csv.DictReader(StringIO(LINES_CSV))
    for row in reader:
        try:
            name = row["name"].strip()
            # Stations are stored as a list of UIDs, which we will resolve to names later
            raw_stations_uids = [int(s) for s in row["stations"].split("|") if s]
            
            # **1. Set Line Color**
            # Line PK is 'name', so passing name as pk is correct here.
            line_obj = Line(pk=name, name=name, color=COLOR_MAP.get(name, "#000000"))
            lines_to_create.append(line_obj)
            
            raw_line_data.append({"line_object": line_obj, "station_uids": raw_stations_uids})
        except Exception as e:
            print(f"[Warn] Skipping malformed line row: {row} -- {e}")
    return lines_to_create, raw_line_data

# --- Data Population Logic ---

def run_populate_logic():
    """Executes the data parsing and M2M relationship setting."""
    
    # 1. Create Stations
    print("[Step] Parsing and creating stations...")
    stations_to_create, uid_to_name_map, final_neighbour_map = parse_stations()
    Station.objects.bulk_create(stations_to_create)
    # Fetch all created station objects, keyed by their PK (name)
    station_objs = {s.pk: s for s in Station.objects.all()}
    print(f"[Info] Created {len(station_objs)} stations.")

    # 2. Create Lines
    print("[Step] Parsing and creating lines...")
    lines_to_create, raw_line_data = parse_lines()
    Line.objects.bulk_create(lines_to_create)
    # Line objects are keyed by their PK (name)
    line_objs = {l.name: l for l in lines_to_create}
    print(f"[Info] Created {len(line_objs)} lines.")

    # 3. Link Stations to Lines
    print("[Step] Setting line-to-station relationships...")
    for item in raw_line_data:
        line_obj = line_objs.get(item["line_object"].pk)
        
        # Convert station UIDs to Names (the primary key for stations)
        station_names = [uid_to_name_map.get(uid) for uid in item["station_uids"] if uid in uid_to_name_map]
        
        # Look up station objects using their Names (PK)
        station_objs_list = [station_objs.get(name) for name in station_names if name]
        
        # **Link stations to their respective lines**
        if line_obj and station_objs_list:
            line_obj.stations.set(station_objs_list)
    print("[Info] Set line-to-station relationships.")

    # 4. Link Neighbouring Stations
    print("[Step] Setting station neighbour relationships...")
    # final_neighbour_map is keyed by station name (PK) and contains neighbour names (PKs)
    for station_name, neighbour_names in final_neighbour_map.items():
        station_obj = station_objs.get(station_name)
        
        # Look up neighbour station objects using their Names (PK)
        neighbour_objs = [station_objs.get(nname) for nname in neighbour_names if nname]
        
        # **Link neighbouring stations**
        if station_obj and neighbour_objs:
            station_obj.neighbours.set(neighbour_objs) 
    print("[Info] Set station neighbour relationships.")
    print("[Success] Data population complete.")

# --- Django Management Command ---

class Command(BaseCommand):
    help = "Populates the database with embedded metro station and line data."

    @transaction.atomic
    def handle(self, *args, **options):
        # Check if data already exists to prevent duplicate population
        station_count = Station.objects.count()
        line_count = Line.objects.count()
        if station_count > 0 or line_count > 0:
            self.stdout.write(self.style.WARNING(
                f"Population skipped: Station records ({station_count}), Line records ({line_count}) already exist."
            ))
            return

        try:
            self.stdout.write(self.style.NOTICE("Starting population of metro database from embedded data..."))
            run_populate_logic()
            self.stdout.write(self.style.SUCCESS("Database populated successfully."))
        except IntegrityError as e:
            self.stderr.write(f"[ERROR] Integrity error during population: {e}")
            raise
        except Exception as e:
            self.stderr.write(f"[ERROR] Unexpected error: {e}")
            raise
