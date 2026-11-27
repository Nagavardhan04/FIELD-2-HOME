from pathlib import Path
import requests
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth

from contextvars import ContextVar

                                                                            
                                                                           
_AUTH_CONTEXT = ContextVar("field2home_auth_context", default=None)

def set_auth_context(id_token, admin_emails=None):
    """Set the verified-session input for the current Streamlit script run."""
    _AUTH_CONTEXT.set({
        "id_token": str(id_token or ""),
        "admin_emails": {str(x).strip().lower() for x in (admin_emails or []) if str(x).strip()},
    })

def clear_auth_context():
    _AUTH_CONTEXT.set(None)

def _require_user(allowed_roles=None):
    """Verify the Firebase ID token and load the authoritative Firestore role."""
    context = _AUTH_CONTEXT.get()
    token = context.get("id_token") if context else None
    if not token:
        raise PermissionError("Your session is missing. Please log in again.")
    app = _get_firebase_app()
    try:
        claims = auth.verify_id_token(token, app=app, check_revoked=True)
    except Exception as exc:
        raise PermissionError("Your login session is invalid or expired. Please log in again.") from exc
    uid = claims.get("uid")
    if not uid:
        raise PermissionError("Unable to verify your account.")
    db = firestore.client(app=app)
    snap = db.collection("user_profiles").document(uid).get()
    if not snap.exists:
        raise PermissionError("Your account profile was not found.")
    profile = snap.to_dict() or {}
    email = str(claims.get("email", profile.get("email", ""))).strip().lower()
    admins = context.get("admin_emails", set()) if context else set()
    role = "admin" if email and email in admins else str(profile.get("role", "customer")).lower()
    if allowed_roles and role not in set(allowed_roles):
        raise PermissionError("Your account is not authorized to perform this action.")
    return {"uid": uid, "email": email, "role": role, "profile": profile, "db": db}



def _get_firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    try:
        service_account_info = st.secrets.get("firebase_service_account")
    except Exception:
        service_account_info = None

    if service_account_info:
        certificate = credentials.Certificate(dict(service_account_info))
    else:
        project_folder = Path(__file__).resolve().parent.parent
        credentials_path = (
            project_folder / "secrets" / "firebase-service-account.json"
        )

        if not credentials_path.is_file():
            raise FileNotFoundError(
                f"Firebase credentials file not found at: {credentials_path}"
            )

        certificate = credentials.Certificate(str(credentials_path))

    return firebase_admin.initialize_app(certificate)


def connect_firebase():
    """Connect to Firestore using the initialized default Firebase app."""
    firebase_app = _get_firebase_app()
    return firestore.client(app=firebase_app)


def _auth_url(endpoint, api_key):
    if not api_key:
        raise ValueError(
            "Firebase Web API key is missing. Add it to .streamlit/secrets.toml."
        )
    return f"https://identitytoolkit.googleapis.com/v1/{endpoint}?key={api_key}"


def _auth_request(endpoint, api_key, payload):
    response = requests.post(
        _auth_url(endpoint, api_key), json=payload, timeout=20
    )
    try:
        result = response.json()
    except ValueError:
        result = {}

    if not response.ok:
        message = result.get("error", {}).get("message", "Authentication failed")
        readable = {
            "EMAIL_EXISTS": "This email is already registered.",
            "INVALID_EMAIL": "Please enter a valid email address.",
            "WEAK_PASSWORD": "Password must contain at least 6 characters.",
            "INVALID_LOGIN_CREDENTIALS": "Incorrect email or password.",
            "EMAIL_NOT_FOUND": "No account exists for this email.",
            "USER_DISABLED": "This account has been disabled.",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Try again later.",
        }
        raise ValueError(readable.get(message, message.replace("_", " ").title()))

    return result


def register_account(email, password, role, full_name, api_key, verified_phone=None):
                                                                        
                                                                         
    role_aliases = {
        "customer": "customer",
        "farmer": "farmer",
        "delivery partner": "delivery_partner",
        "delivery_partner": "delivery_partner",
    }
    role_key = str(role or "").strip().lower().replace("-", " ")
    role = role_aliases.get(role_key)

    if role not in ("customer", "farmer", "delivery_partner"):
        raise ValueError("Choose Customer, Farmer, or Delivery Partner account type.")
    if len(password) < 6:
        raise ValueError("Password must contain at least 6 characters.")
    if not full_name.strip():
        raise ValueError("Please enter your name.")
    if not verified_phone or not str(verified_phone).startswith("+91"):
        raise ValueError("Verify an Indian mobile number with OTP before creating your account.")

    result = _auth_request(
        "accounts:signUp",
        api_key,
        {"email": email.strip(), "password": password, "returnSecureToken": True},
    )

    uid = result["localId"]
    database = connect_firebase()
    database.collection("user_profiles").document(uid).set({
        "uid": uid,
        "email": email.strip().lower(),
        "full_name": full_name.strip(),
        "phone": str(verified_phone),
        "phone_verified": True,
        "role": role,
        "verification_status": "pending" if role in ("farmer", "delivery_partner") else "not_required",
        "created_at": firestore.SERVER_TIMESTAMP,
    })

    return sign_in_account(email, password, api_key)


def sign_in_account(email, password, api_key):
    result = _auth_request(
        "accounts:signInWithPassword",
        api_key,
        {"email": email.strip(), "password": password, "returnSecureToken": True},
    )

                                                                   
                                                        
    firebase_app = _get_firebase_app()
    decoded = auth.verify_id_token(result["idToken"], app=firebase_app)
    uid = decoded["uid"]

    database = firestore.client(app=firebase_app)
    profile_snapshot = (
        database.collection("user_profiles").document(uid).get()
    )

    if not profile_snapshot.exists:
        raise ValueError("Your user profile was not found. Please contact support.")

    profile = profile_snapshot.to_dict() or {}
    return {
        "uid": uid,
        "email": result.get("email", email.strip()),
        "id_token": result["idToken"],
        "full_name": profile.get("full_name", "User"),
        "role": profile.get("role", "customer"),
        "verification_status": profile.get("verification_status", "pending"),
        "phone": profile.get("phone", ""),
        "phone_verified": bool(profile.get("phone_verified", False)),
    }



def sign_in_with_google_id_token(google_id_token, api_key):
    """Exchange a Google ID token for a Firebase session and ensure a user profile exists."""
    if not google_id_token:
        raise ValueError("Google did not return an ID token. Please try again.")

    result = _auth_request(
        "accounts:signInWithIdp",
        api_key,
        {
            "postBody": f"id_token={google_id_token}&providerId=google.com",
            "requestUri": "http://localhost",
            "returnIdpCredential": True,
            "returnSecureToken": True,
        },
    )

    firebase_app = _get_firebase_app()
    decoded = auth.verify_id_token(result["idToken"], app=firebase_app)
    uid = decoded["uid"]
    database = firestore.client(app=firebase_app)
    profile_ref = database.collection("user_profiles").document(uid)
    profile_snapshot = profile_ref.get()

    email = str(result.get("email", decoded.get("email", ""))).strip().lower()
    full_name = str(result.get("displayName") or email.split("@")[0] or "Customer").strip()

    if not profile_snapshot.exists:
        profile_ref.set({
            "uid": uid,
            "email": email,
            "full_name": full_name,
            "role": "customer",
            "verification_status": "not_required",
            "auth_provider": "google.com",
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        profile = {
            "uid": uid,
            "email": email,
            "full_name": full_name,
            "role": "customer",
            "verification_status": "not_required",
        }
    else:
        profile = profile_snapshot.to_dict() or {}
                                                                                               
        updates = {}
        if not profile.get("email") and email:
            updates["email"] = email
        if not profile.get("full_name") and full_name:
            updates["full_name"] = full_name
        if not profile.get("auth_provider"):
            updates["auth_provider"] = "google.com"
        if updates:
            profile_ref.update(updates)
            profile.update(updates)

    return {
        "uid": uid,
        "email": email or profile.get("email", ""),
        "id_token": result["idToken"],
        "full_name": profile.get("full_name", full_name),
        "role": profile.get("role", "customer"),
        "verification_status": profile.get("verification_status", "not_required"),
    }


def get_user_profile(uid):
    user = _require_user({"customer", "farmer", "delivery_partner", "admin"})
    if uid != user["uid"] and user["role"] != "admin":
        raise PermissionError("You can view only your own profile.")
    snapshot = connect_firebase().collection("user_profiles").document(uid).get()
    if not snapshot.exists:
        raise ValueError("User profile was not found.")
    return snapshot.to_dict() or {}


def submit_farmer_verification(uid, application):
    user = _require_user({"farmer"})
    if uid != user["uid"]:
        raise PermissionError("You can submit verification only for your own account.")
    database = connect_firebase()
    reference = database.collection("user_profiles").document(uid)
    snapshot = reference.get()
    if not snapshot.exists or (snapshot.to_dict() or {}).get("role") != "farmer":
        raise PermissionError("Only farmer accounts can submit this application.")
    reference.update({
        "verification_method": application["verification_method"],
        "verification_reference_last4": application["reference_last4"],
        "farm_state": application["farm_state"],
        "farm_district": application["farm_district"],
        "verification_status": "pending",
        "verification_submitted_at": firestore.SERVER_TIMESTAMP,
        "admin_note": "",
    })


def get_pending_farmer_applications():
    user = _require_user({"admin"})
    database = connect_firebase()
    results = []
    query = database.collection("user_profiles").where("role", "==", "farmer")
    for doc in query.stream():
        item = doc.to_dict() or {}
        if item.get("verification_status") == "pending":
            item["uid"] = doc.id
            results.append(item)
    return results


def review_farmer_application(uid, decision, admin_note):
    user = _require_user({"admin"})
    if decision not in ("approved", "rejected"):
        raise ValueError("Invalid verification decision.")
    database = connect_firebase()
    reference = database.collection("user_profiles").document(uid)
    snapshot = reference.get()
    if not snapshot.exists or (snapshot.to_dict() or {}).get("role") != "farmer":
        raise ValueError("Farmer application was not found.")
    reference.update({
        "verification_status": decision,
        "admin_note": admin_note.strip(),
        "verification_reviewed_at": firestore.SERVER_TIMESTAMP,
    })


def add_product_to_database(product):
    user = _require_user({"farmer"})
    if user["profile"].get("verification_status") != "approved":
        raise PermissionError("Only approved farmers can list products.")
    product = dict(product or {})
    product["owner_uid"] = user["uid"]
    database = connect_firebase()
    document = database.collection("products").document()
    document.set(product)
    return document.id


def get_products_from_database():
    database = connect_firebase()
    product_list = []
    for document in database.collection("products").stream():
        product = document.to_dict() or {}
        product["id"] = document.id
        product_list.append(product)
    return product_list


def get_farmer_products(uid):
    user = _require_user({"farmer"})
    if uid != user["uid"]:
        raise PermissionError("You can view only your own products.")
    database = connect_firebase()
    product_list = []
    documents = database.collection("products").where("owner_uid", "==", uid).stream()
    for document in documents:
        product = document.to_dict() or {}
        product["id"] = document.id
        product_list.append(product)
    return product_list


def update_product_in_database(product_id, updated_data, owner_uid):
    user = _require_user({"farmer"})
    if owner_uid != user["uid"]:
        raise PermissionError("You can edit only your own products.")
    if user["profile"].get("verification_status") != "approved":
        raise PermissionError("Only approved farmers can manage products.")
    forbidden = {"owner_uid", "id", "created_at"}
    if forbidden.intersection(updated_data):
        raise ValueError("Protected product fields cannot be changed.")
    database = connect_firebase()
    reference = database.collection("products").document(product_id)
    snapshot = reference.get()
    if not snapshot.exists or (snapshot.to_dict() or {}).get("owner_uid") != owner_uid:
        raise PermissionError("You can only edit products listed by your account.")
    reference.update(updated_data)
    return True


def delete_product_from_database(product_id, owner_uid):
    user = _require_user({"farmer"})
    if owner_uid != user["uid"]:
        raise PermissionError("You can delete only your own products.")
    if user["profile"].get("verification_status") != "approved":
        raise PermissionError("Only approved farmers can manage products.")
    database = connect_firebase()
    reference = connect_firebase().collection("products").document(product_id)
    snapshot = reference.get()
    if not snapshot.exists or (snapshot.to_dict() or {}).get("owner_uid") != owner_uid:
        raise PermissionError("You can only delete products listed by your account.")
    reference.delete()
    return True


def create_order(customer_uid, customer_name, customer_email, phone,
                 address, items, payment_method="Cash on Delivery"):
    user = _require_user({"customer"})
    if customer_uid != user["uid"]:
        raise PermissionError("You can place orders only for your own account.")
    profile = user["profile"]
    customer_uid = user["uid"]
    customer_email = user["email"] or profile.get("email", "")
    customer_name = str(customer_name or profile.get("full_name", "Customer")).strip()
    """
    Create an order and decrement stock in a Firestore transaction.
    The transaction prevents two customers from buying more than available stock.
    """
    if not items:
        raise ValueError("Your cart is empty.")

    database = connect_firebase()
    order_ref = database.collection("orders").document()
    product_refs = [
        database.collection("products").document(str(item["product_id"]))
        for item in items
    ]
    transaction = database.transaction()

    @firestore.transactional
    def _place_order(transaction):
                                                                            
                                                                         
        snapshots = [next(transaction.get(ref), None) for ref in product_refs]
        checked_items = []
        total = 0.0

                                                              
        for item, snapshot in zip(items, snapshots):
            if snapshot is None or not snapshot.exists:
                raise ValueError(f"{item.get('name', 'A product')} is no longer available.")

            product = snapshot.to_dict() or {}
            try:
                available_stock = int(product.get("stock", 0))
                quantity = int(item.get("quantity", 0))
                price = float(product.get("price", 0))
            except (TypeError, ValueError):
                raise ValueError("A product has invalid price or stock information.")

            if quantity < 1:
                raise ValueError("Order quantity must be at least one.")
            if available_stock < quantity:
                raise ValueError(
                    f"Insufficient stock for {product.get('name', 'a product')}. "
                    f"Available stock: {available_stock}."
                )

                                                                                  
            checked_item = {
                "product_id": item["product_id"],
                "name": product.get("name", "Product"),
                "farmer": product.get("farmer", ""),
                "owner_uid": product.get("owner_uid", ""),
                "price": price,
                "quantity": quantity,
                "unit": product.get("quantity", ""),
                "item_status": "placed",
            }
            checked_items.append(checked_item)
            total += price * quantity

        for ref, snapshot, item in zip(product_refs, snapshots, checked_items):
            current_stock = int((snapshot.to_dict() or {}).get("stock", 0))
            transaction.update(ref, {"stock": current_stock - item["quantity"]})

        order_data = {
            "order_id": order_ref.id,
            "customer_uid": customer_uid,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "phone": phone,
            "address": address,
            "items": checked_items,
            "total": round(total, 2),
            "payment_method": payment_method,
            "payment_status": "pending",
            "status": "placed",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
        transaction.set(order_ref, order_data)

    _place_order(transaction)
    return order_ref.id


def get_customer_orders(customer_uid):
    user = _require_user({"customer", "admin"})
    if customer_uid != user["uid"] and user["role"] != "admin":
        raise PermissionError("You can view only your own orders.")
    database = connect_firebase()
    orders = []
    query = (
        database.collection("orders")
        .where("customer_uid", "==", customer_uid)
        .stream()
    )
    for doc in query:
        order = doc.to_dict() or {}
        order["order_id"] = doc.id
        orders.append(order)
    orders.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    return orders


def get_farmer_orders(farmer_uid):
    user = _require_user({"farmer"})
    if farmer_uid != user["uid"]:
        raise PermissionError("You can view orders for your own farmer account only.")
    if user["profile"].get("verification_status") != "approved":
        raise PermissionError("Only approved farmers can view farmer orders.")
    """Return orders containing at least one product owned by this farmer."""
    database = connect_firebase()
    orders = []
    for doc in database.collection("orders").stream():
        order = doc.to_dict() or {}
        farmer_items = [
            item for item in order.get("items", [])
            if item.get("owner_uid") == farmer_uid
        ]
        if farmer_items:
            order["order_id"] = doc.id
            orders.append(order)
    return orders


def update_farmer_order_item_status(order_id, product_id, farmer_uid, new_status):
    user = _require_user({"farmer"})
    if farmer_uid != user["uid"]:
        raise PermissionError("You can update only your own farmer orders.")
    if user["profile"].get("verification_status") != "approved":
        raise PermissionError("Only approved farmers can update orders.")
    allowed_statuses = {
        "confirmed", "processing", "ready_for_pickup",
        "out_for_delivery", "delivered"
    }
    if new_status not in allowed_statuses:
        raise ValueError("Invalid order status.")

    database = connect_firebase()
    reference = database.collection("orders").document(order_id)
    snapshot = reference.get()
    if not snapshot.exists:
        raise ValueError("Order was not found.")

    order = snapshot.to_dict() or {}
    items = order.get("items", [])
    found = False

    for item in items:
        if item.get("product_id") == product_id:
            if item.get("owner_uid") != farmer_uid:
                raise PermissionError("You can only update orders for your own products.")
            item["item_status"] = new_status
            found = True

    if not found:
        raise ValueError("This product was not found in the order.")

    statuses = [item.get("item_status", "placed") for item in items]
    if statuses and all(status == "delivered" for status in statuses):
        overall_status = "delivered"
    elif "out_for_delivery" in statuses:
        overall_status = "out_for_delivery"
    elif "ready_for_pickup" in statuses:
        overall_status = "ready_for_pickup"
    elif "processing" in statuses:
        overall_status = "processing"
    elif "confirmed" in statuses:
        overall_status = "confirmed"
    else:
        overall_status = "placed"

    reference.update({
        "items": items,
        "status": overall_status,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })
    return True


def get_all_orders():
    user = _require_user({"admin"})
    database = connect_firebase()
    orders = []
    for doc in database.collection("orders").stream():
        order = doc.to_dict() or {}
        order["order_id"] = doc.id
        orders.append(order)
    return orders


                                                           
                             
                                                           

def get_pending_delivery_partners():
    user = _require_user({"admin"})
    database = connect_firebase()
    results = []
    query = database.collection("user_profiles").where("role", "==", "delivery_partner")
    for doc in query.stream():
        profile = doc.to_dict() or {}
        if profile.get("verification_status") == "pending":
            profile["uid"] = doc.id
            results.append(profile)
    return results


def review_delivery_partner(uid, decision, admin_note=""):
    user = _require_user({"admin"})
    if decision not in ("approved", "rejected"):
        raise ValueError("Invalid delivery partner decision.")
    reference = connect_firebase().collection("user_profiles").document(uid)
    snapshot = reference.get()
    profile = snapshot.to_dict() or {} if snapshot.exists else {}
    if not snapshot.exists or profile.get("role") != "delivery_partner":
        raise ValueError("Delivery partner application was not found.")
    reference.update({
        "verification_status": decision,
        "admin_note": admin_note.strip(),
        "verification_reviewed_at": firestore.SERVER_TIMESTAMP,
    })


def get_approved_delivery_partners():
    user = _require_user({"admin"})
    database = connect_firebase()
    partners = []
    query = database.collection("user_profiles").where("role", "==", "delivery_partner")
    for doc in query.stream():
        profile = doc.to_dict() or {}
        if profile.get("verification_status") == "approved":
            profile["uid"] = doc.id
            partners.append(profile)
    return partners


def assign_order_to_delivery_partner(order_id, partner_uid, admin_uid):
    user = _require_user({"admin"})
    if admin_uid != user["uid"]:
        raise PermissionError("Administrator identity mismatch.")
    database = connect_firebase()
    partner_ref = database.collection("user_profiles").document(partner_uid)
    partner_snapshot = partner_ref.get()
    partner = partner_snapshot.to_dict() or {} if partner_snapshot.exists else {}
    if not partner_snapshot.exists or partner.get("role") != "delivery_partner" or partner.get("verification_status") != "approved":
        raise PermissionError("Only an approved delivery partner can receive an order.")

    order_ref = database.collection("orders").document(order_id)
    order_snapshot = order_ref.get()
    if not order_snapshot.exists:
        raise ValueError("Order was not found.")
    order = order_snapshot.to_dict() or {}
    if order.get("status") == "delivered":
        raise ValueError("This order has already been delivered.")
    if order.get("delivery_partner_uid"):
        raise ValueError("This order is already assigned to a delivery partner.")
    if not any(item.get("item_status") == "ready_for_pickup" for item in order.get("items", [])):
        raise ValueError("At least one item must be ready for pickup before assignment.")

    order_ref.update({
        "delivery_partner_uid": partner_uid,
        "delivery_partner_name": partner.get("full_name", "Delivery Partner"),
        "delivery_assigned_by": admin_uid,
        "delivery_assigned_at": firestore.SERVER_TIMESTAMP,
        "delivery_status": "assigned",
        "updated_at": firestore.SERVER_TIMESTAMP,
    })


def get_delivery_partner_orders(partner_uid):
    user = _require_user({"delivery_partner"})
    if partner_uid != user["uid"]:
        raise PermissionError("You can view only deliveries assigned to your account.")
    if user["profile"].get("verification_status") != "approved":
        raise PermissionError("Only approved delivery partners can view deliveries.")
    database = connect_firebase()
    results = []
    query = database.collection("orders").where("delivery_partner_uid", "==", partner_uid)
    for doc in query.stream():
        order = doc.to_dict() or {}
        order["order_id"] = doc.id
        results.append(order)
    return results


def update_delivery_status(order_id, partner_uid, new_status, note=""):
    user = _require_user({"delivery_partner"})
    if partner_uid != user["uid"]:
        raise PermissionError("You can update only deliveries assigned to your account.")
    if user["profile"].get("verification_status") != "approved":
        raise PermissionError("Only approved delivery partners can update deliveries.")
    allowed = {"accepted", "picked_up", "out_for_delivery", "delivered"}
    if new_status not in allowed:
        raise ValueError("Invalid delivery status.")

    reference = connect_firebase().collection("orders").document(order_id)
    snapshot = reference.get()
    if not snapshot.exists:
        raise ValueError("Order was not found.")
    order = snapshot.to_dict() or {}
    if order.get("delivery_partner_uid") != partner_uid:
        raise PermissionError("You can update only orders assigned to your account.")

    reference.update({
        "delivery_status": new_status,
        "delivery_note": note.strip(),
        "delivery_status_updated_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
        **({"status": "delivered"} if new_status == "delivered" else {}),
    })
