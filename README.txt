FIELD 2 HOME - DELIVERY PARTNER UI UPDATE

This update changes only the Delivery Partner dashboard presentation:
- Formats dictionary-based delivery addresses into readable fields.
- Adds a Google Maps navigation button using saved GPS coordinates, or the address as a fallback.
- Shows ordered products and quantities in the delivery card.
- Supports older orders whose address is stored as plain text.

No Firebase collections, existing orders, login code, service-account files, or secrets are changed.

INSTALLATION (Windows PowerShell)
1. Stop Streamlit with Ctrl+C.
2. Make a backup of your current app.py:
   Copy-Item .\app.py .\app.py.backup_delivery_ui
3. Extract this ZIP into your FIELD_2_HOME project folder, allowing app.py to be replaced.
4. Start the app:
   python -m streamlit run app.py
5. Log in as an approved delivery partner and open Delivery Partner.

If anything goes wrong, restore the backup:
   Copy-Item .\app.py.backup_delivery_ui .\app.py -Force
   python -m streamlit run app.py

Note: Google Maps navigation opens a route in Google Maps. It does not provide live GPS tracking inside this Streamlit app.
