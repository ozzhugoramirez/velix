import environ
import requests

# Inicializar el entorno
env = environ.Env()
environ.Env.read_env()  # Cargar el archivo .env


def send_whatsapp_message(whatsapp_number, template_name, parameters, verification_code):
    if not whatsapp_number.startswith("54"):
        whatsapp_number = "54" + whatsapp_number

    url = env('WHATSAPP_API_URL')
    token = env('WHATSAPP_API_TOKEN')

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": whatsapp_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "es"},
            "components": [
                {
                    "type": "body",
                    "parameters": parameters
                },
                {
                    "type": "button",
                    "sub_type": "url",  # Cambiar a tipo URL
                    "index": 0,
                    "parameters": [
                        {
                            "type": "text",
                            "text": f"{verification_code}"  # URL con el código
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()
