from services.firebase_service import connect_firebase

try:

    database = connect_firebase()

    print("================================")

    print("FIELD 2 HOME")

    print("FIREBASE CONNECTION SUCCESSFUL")

    print("================================")

    print("Database connected successfully.")

except Exception as error:

    print("Firebase connection failed.")

    print(error)