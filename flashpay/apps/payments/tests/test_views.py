from uuid import UUID

import pytest

from django.conf import settings

from rest_framework.test import APIClient

from flashpay.apps.account.models import Account, APIKey
from flashpay.apps.core.models import Asset
from flashpay.apps.payments.models import Network, PaymentLink, Transaction, TransactionStatus
from flashpay.apps.payments.tasks import calculate_daily_revenue


@pytest.mark.django_db
def test_payment_link_crud_no_auth(api_client: APIClient) -> None:
    """Tests PaymentLink CRUD Endpoints without Authentication."""
    # Create Payment Link
    response1 = api_client.post("/api/payment-links")
    assert response1.status_code == 401

    # Fetch Payment Links
    response2 = api_client.get("/api/payment-links")
    assert response2.status_code == 401

    # Retreive Payment Link returns 404 as it can be access when there's no auth.
    response3 = api_client.get("/api/payment-links/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response3.status_code == 404

    # Active | Inactive Update Test
    response5 = api_client.patch("/api/payment-links/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response5.status_code == 401

    # Fetch Transactions Endpoint
    response6 = api_client.get("/api/transactions?slug=4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response6.status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_payment_link_crud_secret_key_auth(
    secret_key_api_client: APIClient,
    account_api_key: APIKey,
    algo_asa: Asset,
) -> None:
    """
    Tests Payment Link CRUD Endpoints with secret key authentication.
    """
    data = {
        "name": "Test",
        "description": "test",
        "asset": algo_asa.asa_id,
        "amount": 40,
    }
    response = secret_key_api_client.post("/api/payment-links", data=data)
    assert response.status_code == 201
    assert "Payment Link Created Successfully" in response.data["message"]

    # check that the created link is present in db
    payment_link = PaymentLink.objects.first()
    assert payment_link is not None

    # retrieve all links
    response = secret_key_api_client.get("/api/payment-links")
    assert response.status_code == 200
    assert len(response.data["data"]["results"]) == 1

    # Retrieve Payment Link
    response = secret_key_api_client.get(f"/api/payment-links/{payment_link.slug}")
    assert response.status_code == 200
    assert response.data["data"]["image_url"] == settings.DEFAULT_PAYMENT_LINK_IMAGE
    assert "total_revenue" in response.data["data"]
    assert response.data["message"] == "Payment Link returned successfully"

    # Retrieve Payment Link 404
    response = secret_key_api_client.get("/api/payment-links/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response.status_code == 404
    assert "No PaymentLink matches the given query." in response.data["message"]

    # Active | Inactive Update Test
    response = secret_key_api_client.patch(f"/api/payment-links/{payment_link.slug}")
    assert response.status_code == 200
    assert response.data["data"]["is_active"] is False
    assert "Payment Link Updated" in response.data["message"]

    # Fetch Transactions Endpoint
    response = secret_key_api_client.get("/api/transactions", {"payment_link": payment_link.uid})
    assert response.status_code == 200
    assert len(response.data["data"]["results"]) == 0
    assert "Transactions returned successfully" in response.data["message"]


@pytest.mark.django_db
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_payment_link_crud_custom_jwt_auth(
    jwt_api_client: APIClient,
    algo_asa: Asset,
) -> None:
    """
    Tests Payment Link CRUD Endpoints with JWT Authentication.
    """
    data = {
        "name": "Test",
        "description": "test",
        "asset": algo_asa.asa_id,
        "amount": 40,
    }
    response = jwt_api_client.post("/api/payment-links", data=data)
    assert response.status_code == 201
    assert "Payment Link Created Successfully" == response.data["message"]

    # check that the created link is present in db
    payment_link = PaymentLink.objects.first()
    assert payment_link is not None

    # retrieve all links
    response = jwt_api_client.get("/api/payment-links")
    assert response.status_code == 200
    assert len(response.data["data"]["results"]) == 1

    # Retrieve Payment Link
    response = jwt_api_client.get(f"/api/payment-links/{payment_link.slug}")
    assert response.status_code == 200
    assert response.data["data"]["image_url"] == settings.DEFAULT_PAYMENT_LINK_IMAGE
    assert response.data["message"] == "Payment Link returned successfully"

    # Retrieve Payment Link 404
    response = jwt_api_client.get("/api/payment-links/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response.status_code == 404
    assert "No PaymentLink matches the given query." in response.data["message"]

    # Active | Inactive Update Test
    response = jwt_api_client.patch(f"/api/payment-links/{payment_link.slug}")
    assert response.status_code == 200
    assert response.data["data"]["is_active"] is False
    assert "Payment Link Updated" in response.data["message"]

    # Fetch Transactions Endpoint
    response = jwt_api_client.get(f"/api/transactions?payment_link={payment_link.uid}")
    assert response.status_code == 200
    assert len(response.data["data"]["results"]) == 0
    assert "Transactions returned successfully" in response.data["message"]


@pytest.mark.django_db
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_create_payment_link_no_amount_and_zero_amount(
    jwt_api_client: APIClient,
    algo_asa: Asset,
) -> None:
    data = {
        "name": "Test",
        "description": "test",
        "asset": algo_asa.asa_id,
    }
    response = jwt_api_client.post("/api/payment-links", data=data)
    assert response.status_code == 400
    assert response.data["message"] == "Validation Error"
    assert response.data["data"]["amount"][0] == "This field is required."

    data2 = {
        "name": "Test",
        "description": "test",
        "asset": algo_asa.asa_id,
        "amount": 0,
    }
    response = jwt_api_client.post("/api/payment-links", data=data2)
    assert response.status_code == 400
    assert response.data["message"] == "Validation Error"
    assert response.data["data"]["amount"][0] == "Amount cannot be less than or equal to zero."


@pytest.mark.django_db
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_initialize_transaction_invalid_address(
    secret_key_api_client: APIClient,
    algo_asa: Asset,
    account: Account,
) -> None:
    payment_link = PaymentLink.objects.create(
        name="Test Link",
        description="test",
        asset=algo_asa,
        amount=200,
        account=account,
    )

    data = {
        "amount": 100,
        "asset": algo_asa.asa_id,
        "payment_link": payment_link.uid,
        "txn_type": "payment_link",
        "recipient": "3UECD5MS3SEOM64LOWB5GFWDZM7IPBQOUG4AQPAIYEYOIXOOFCQXYUSKVW",
        "sender": "7IPBQOUG4AQPAIYEYOIXOOFCQXYUSKVW3UECD5MS3SEOM64LOWB5GFWDZM",
    }
    response = secret_key_api_client.post("/api/transactions", data=data)
    assert response.status_code == 400
    assert response.data["message"] == "Validation Error"
    assert response.data["data"]["sender"][0] == "Not a valid address"


@pytest.mark.django_db
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_initialize_transaction_wrong_amount(
    secret_key_api_client: APIClient,
    algo_asa: Asset,
    account: Account,
) -> None:
    payment_link = PaymentLink.objects.create(
        name="Test Link",
        description="test",
        asset=algo_asa,
        amount=100,
        has_fixed_amount=True,
        account=account,
    )

    data = {
        "amount": 50,
        "asset": algo_asa.asa_id,
        "payment_link": payment_link.uid,
        "txn_type": "payment_link",
        "recipient": payment_link.account.address,  # type: ignore
        "sender": "XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    }
    response = secret_key_api_client.post("/api/transactions", data=data)
    assert response.status_code == 400
    assert response.data["data"]["amount"][0] == "payment link has fixed amount"


@pytest.mark.django_db
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_initialize_transaction_wrong_asset(
    secret_key_api_client: APIClient,
    algo_asa: Asset,
    usdc_asa: Asset,
    account: Account,
) -> None:
    payment_link = PaymentLink.objects.create(
        name="Test Link",
        description="test",
        asset=usdc_asa,
        amount=100,
        has_fixed_amount=True,
        account=account,
    )

    data = {
        "amount": 100,
        "asset": algo_asa.asa_id,
        "payment_link": payment_link.uid,
        "txn_type": "payment_link",
        "recipient": payment_link.account.address,  # type: ignore
        "sender": "XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    }
    response = secret_key_api_client.post("/api/transactions", data=data)
    assert response.status_code == 400
    assert response.data["data"]["asset"][0] == "payment link asset does not match specified asset"


@pytest.mark.django_db
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_initialize_transaction_recipient_not_opted_in(
    secret_key_api_client: APIClient,
    usdt_asa: Asset,
    account: Account,
) -> None:
    payment_link = PaymentLink.objects.create(
        name="Test Link",
        description="test",
        asset=usdt_asa,
        amount=100,
        account=account,
    )

    data = {
        "amount": 50,
        "asset": usdt_asa.asa_id,
        "payment_link": payment_link.uid,
        "txn_type": "payment_link",
        "recipient": payment_link.account.address,  # type: ignore
        "sender": "XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    }
    response = secret_key_api_client.post("/api/transactions", data=data)
    assert response.status_code == 400
    assert response.data["data"]["recipient"][0] == "recipient is not opted in to the asset."


@pytest.mark.django_db
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_initialize_transaction(
    secret_key_api_client: APIClient,
    account: Account,
    algo_asa: Asset,
    network: Network,
) -> None:
    payment_link = PaymentLink.objects.create(
        name="Test Link",
        description="test",
        asset=algo_asa,
        amount=200,
        account=account,
    )

    # Fetch all transactions Endpoint
    response = secret_key_api_client.get("/api/transactions")
    assert response.status_code == 200
    assert len(response.data["data"]["results"]) == 0
    assert "Transactions returned successfully" in response.data["message"]

    # Fetch payment link transactions 404
    response = secret_key_api_client.get(
        "/api/transactions?slug=04e88d1a-ee77-4c46-86a9-6636859c6571"
    )
    assert response.status_code == 404

    # Create Payment Link Transaction
    data = {
        "amount": 100,
        "asset": algo_asa.asa_id,
        "payment_link": payment_link.uid,
        "txn_type": "payment_link",
        "recipient": payment_link.account.address,  # type: ignore
        "sender": "XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    }
    response = secret_key_api_client.post("/api/transactions", data=data)
    assert response.status_code == 201
    assert "Transaction created successfully" in response.data["message"]
    if network == Network.TESTNET:
        assert response.data["data"]["asset"]["asa_id"] == 0
    else:
        assert response.data["data"]["asset"]["asa_id"] == 1
    assert response.data["data"]["asset"]["short_name"] == "ALGO"
    assert response.data["data"]["asset"]["long_name"] == "Algorand"

    # check that the created link is present in db
    transaction = Transaction.objects.first()
    assert transaction is not None

    # Fetch all transactions Endpoint
    response = secret_key_api_client.get("/api/transactions")
    assert response.status_code == 200
    assert len(response.data["data"]["results"]) == 1
    assert "Transactions returned successfully" in response.data["message"]

    # Fetch payment link transactions Endpoint slug
    response = secret_key_api_client.get(f"/api/transactions?slug={payment_link.slug}")
    assert response.status_code == 200
    assert len(response.data["data"]["results"]) == 1
    assert "Transactions returned successfully" in response.data["message"]


@pytest.mark.django_db
@pytest.mark.parametrize("is_account_opted_in", [True])
def test_verify_transaction_usdc(
    secret_key_api_client: APIClient,
    usdc_asa: Asset,
    account: Account,
) -> None:
    # Create Payment Link
    payment_link = PaymentLink.objects.create(
        uid=UUID("399c37cb-d282-4aed-8917-38a033a1ad5b"),
        name="Test Link",
        description="test",
        asset=usdc_asa,
        amount=10,
        account=account,
    )

    # fp_399c37cbd2824aed891738a033a1ad5b_03ef72
    tx_ref = "fp_" + payment_link.uid.hex + "_03ef72"

    # Create Payment link transaction
    Transaction.objects.create(
        txn_reference=tx_ref,
        txn_type="payment_link",
        amount=10,
        asset=usdc_asa,
        recipient=str(payment_link.account.address),  # type: ignore
        sender="XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    )

    # Verify transaction
    # https://testnet.algoexplorer.io/tx/F23RSTSTWEWMX3LWZ3ZEUHRWFPOIXXAPOWS2DJ7YHK5NC3VKKTDA
    response = secret_key_api_client.post(f"/api/transactions/verify/{tx_ref}")
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("is_account_opted_in", [True])
def test_verify_transaction_usdt(
    secret_key_api_client: APIClient,
    account: Account,
    usdt_asa: Asset,
) -> None:
    # Create Payment Link
    payment_link = PaymentLink.objects.create(
        uid=UUID("90de70d9-bfd9-4596-8ab4-c06aa8e35bcd"),
        name="Test Link",
        description="test",
        asset=usdt_asa,
        amount=10,
        account=account,
    )

    # fp_90de70d9bfd945968ab4c06aa8e35bcd_03ef72
    tx_ref = "fp_" + payment_link.uid.hex + "_03ef72"

    # Create Payment link transaction
    Transaction.objects.create(
        txn_reference=tx_ref,
        txn_type="payment_link",
        amount=2,
        asset=usdt_asa,
        recipient=str(payment_link.account.address),  # type: ignore
        sender="XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    )

    # Verify transaction
    # https://testnet.algoexplorer.io/tx/LB5YIOTIYDY34EOC4DMWPELL2VYPWFGQIF2JKINBA6FPPOKXEA4Q
    response = secret_key_api_client.post(f"/api/transactions/verify/{tx_ref}")
    assert response.status_code == 200


@pytest.mark.django_db
def test_verify_transaction_algo(
    secret_key_api_client: APIClient,
    account: Account,
    algo_asa: Asset,
) -> None:
    # Create Payment Link
    payment_link = PaymentLink.objects.create(
        uid=UUID("c96a73fc-de56-405b-ac45-03b09196d123"),
        name="Test Link",
        description="test",
        asset=algo_asa,
        amount=10,
        account=account,
        has_fixed_amount=True,
    )

    # fp_c96a73fcde56405bac4503b09196d123_03ef72
    tx_ref = "fp_" + payment_link.uid.hex + "_03ef72"

    # Create Payment link transaction
    Transaction.objects.create(
        txn_reference=tx_ref,
        txn_type="payment_link",
        amount=10,
        asset=algo_asa,
        recipient=str(payment_link.account.address),  # type: ignore
        sender="XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    )

    # Verify transaction
    # https://testnet.algoexplorer.io/tx/EPOEON47C2NANNPC5FJLRU42R7SZ6KT5HDO5B6OEJE7G4VQBDXIA
    response = secret_key_api_client.post(f"/api/transactions/verify/{tx_ref}")
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("is_account_opted_in", [True])
def test_verify_transaction_with_wrong_txn_hash_and_txn_note(
    account: Account,
    secret_key_api_client: APIClient,
    choice_asa: Asset,
) -> None:
    # Create Payment Link
    payment_link = PaymentLink.objects.create(
        uid=UUID("3fe0321e-c44e-44ad-b03a-0348ad7d6f78"),
        name="Test Link",
        description="test",
        asset=choice_asa,
        amount=200,
        account=account,
    )

    # fp_3fe0321ec44e44adb03a0348ad7d6f78_03ef72
    tx_ref = "fp_" + payment_link.uid.hex + "_03ef72"

    # Create Payment link transaction
    Transaction.objects.create(
        txn_reference=tx_ref,
        txn_type="payment_link",
        amount=20,
        asset=choice_asa,
        recipient=account.address,
        sender="XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    )

    # Verify transaction with wrong tx reference
    tx_ref = "fp_" + payment_link.uid.hex + "_03eabc"
    response = secret_key_api_client.post(f"/api/payment-links/transactions/verify/{tx_ref}")
    assert response.status_code == 404
    assert (
        "Not Found: /api/payment-links/transactions/verify/fp_3fe0321ec44e44adb03a0348ad7d6f78_03eabc"  # noqa: E501
        in response.json()["message"]  # type: ignore  # noqa: E501 it returns JsonResponse not Response so there's no `.data`
    )


@pytest.mark.django_db
@pytest.mark.parametrize("is_account_opted_in", [True])
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_daily_revenue(
    jwt_api_client: APIClient, account: Account, usdc_asa: Asset, network: Network
) -> None:
    # Create Transactions
    Transaction.objects.create(
        txn_reference="fp_hello_hii",
        txn_type="payment_link",
        amount=100,
        asset=usdc_asa,
        recipient=str(account.address),
        status=TransactionStatus.SUCCESS,
        sender="XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    )

    # Calculate Daily Revenue
    calculate_daily_revenue(network)

    response = jwt_api_client.get(f"/api/daily-revenue?asa_id={usdc_asa.asa_id}")
    assert response.status_code == 200
    assert len(response.data["data"]) == 1
