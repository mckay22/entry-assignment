 #Summary 
DB_USERNAME and DB_PASSWORD are stored in environment variable\
configClear_v2.json is in assignment folder\
I decided to use Class which represents Interface for grouping all data that should be inserted into database.\
Based on assignment we can easily Include or exclude other interfaces through class attribute list "exclude_interfaces"

Also I decided to use Class design for managing access to the database, so I could avoid passing reference for cursor and connection to the functions

 #Problems
At the beginning I couldn't read configClear_v2.json because I was getting error "JSON standard does not allow trailing comma" at line 1888 column 29, 
so I manually removed that comma.