import openai
import re
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from .models import BotConfig, BotKnowledge, ChatMessage, ChatIncident
from apps.shops.models import Product

# Configuración del cliente OpenAI
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def get_session_id(request):
    """Obtiene o crea un ID para anónimos"""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

def check_for_incidents(text, user, session_id):
    """Detecta insultos básicos y guarda incidente."""
    bad_words = ['estafa', 'ladrones', 'basura', 'inutil', 'idiota', 'odio', 'robo', 'mierda'] 
    text_lower = text.lower()
    
    for word in bad_words:
        if word in text_lower:
            try:
                ChatIncident.objects.create(
                    user=user, 
                    session_id=session_id,
                    message_content=text,
                    incident_type='INSULT' if 'estafa' not in word else 'CLAIM'
                )
                return True
            except: pass
    return False

def get_product_from_url(url):
    """
    Intenta extraer el ID del producto desde la URL actual del usuario.
    Busca patrones de UUID (ej: ad0999e7-25e4-4e50...)
    """
    try:
        # Regex para UUID estándar
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        match = re.search(uuid_pattern, url)
        
        # Verificamos que la URL contenga 'shops' o 'product' para evitar falsos positivos
        if match and ('shop' in url or 'product' in url):
            product_id = match.group(0)
            # Buscamos el producto en la BD (solo si tiene stock)
            return Product.objects.filter(id=product_id, stock__gt=0).first()
    except Exception as e:
        print(f"Error analizando URL: {e}")
    return None

def chatbot_message(request):
    if request.method == "POST":
        user_message = request.POST.get('message', '')
        current_url = request.POST.get('current_url', '') # <--- NUEVO: Recibimos la URL
        
        # 1. IDENTIFICACIÓN
        session_id = get_session_id(request)
        user = request.user if request.user.is_authenticated else None

        # 2. GUARDAR LOG
        ChatMessage.objects.create(
            user=user,
            session_id=session_id if not user else None,
            role='user',
            content=user_message
        )

        # 3. MODERACIÓN
        check_for_incidents(user_message, user, session_id)

        # 4. HISTORIAL
        if user:
            history_qs = ChatMessage.objects.filter(user=user).order_by('-timestamp')[:8]
        else:
            history_qs = ChatMessage.objects.filter(session_id=session_id).order_by('-timestamp')[:8]
        history_messages = [{"role": msg.role, "content": msg.content} for msg in reversed(history_qs)]

        # 5. PREPARAR DATOS (RAG Contextual)
        
        # A) Configuración Base
        config = BotConfig.objects.first()
        personality = config.personality if config else "Eres OLO, Soporte NextGen."
        restrictions = config.restrictions if config else "Solo temas de la tienda."

        # B) Conocimiento General (Siempre disponible)
        knowledge_text = ""
        knowledge_qs = BotKnowledge.objects.all()
        for k in knowledge_qs:
            knowledge_text += f"- {k.topic}: {k.content}\n"

        # C) URLs Dinámicas
        try:
            link_whatsapp = request.build_absolute_uri(reverse('grupo_whatsapp'))
            link_reclamos = request.build_absolute_uri(reverse('reclamo_create'))
            link_ayuda = request.build_absolute_uri(reverse('info_page_ayuda', kwargs={'section': 'general'}))
        except:
            link_whatsapp = "/whatsapp/"
            link_reclamos = "/reclamo/"
            link_ayuda = "/ayuda/"

        # D) DETECCIÓN DE CONTEXTO (Magia aquí)
        active_product = get_product_from_url(current_url)
        
        if active_product:
            # === CASO 1: CLIENTE VIENDO UN PRODUCTO ===
            system_prompt = f"""
            ROL: {personality}
            CONTEXTO ACTUAL: El cliente está mirando AHORA MISMO la página del producto: "{active_product.title}".
            
            TU OBJETIVO: Actúa como un vendedor experto de ESTE producto específico. Resuelve dudas y motiva la compra.
            
            FICHA TÉCNICA DEL PRODUCTO (Úsala para responder):
            - Nombre: {active_product.title}
            - Precio: ${active_product.price}
            - Descripción Detallada: {active_product.description}
            - Stock: {active_product.stock} unidades
            
            INFORMACIÓN GENERAL (Envíos/Pagos):
            {knowledge_text}
            
            INSTRUCCIONES:
            1. Si preguntan precio o características, usa la Ficha Técnica.
            2. NO menciones otros productos a menos que pregunten. Concéntrate en este.
            3. Si piden contacto: <a href='{link_whatsapp}' target='_blank' class='btn-whatsapp-chat'><i class='bi bi-whatsapp'></i> Consultar por WhatsApp</a>
            """
        else:
            # === CASO 2: GENERAL (Home, Perfil, etc.) ===
            # AQUÍ QUITAMOS LA LISTA DE PRODUCTOS para evitar el texto largo
            system_prompt = f"""
            ROL: {personality}
            CONTEXTO: El cliente está navegando por la tienda (Inicio o Secciones Generales).
            
            TU CONOCIMIENTO (Soporte):
            {knowledge_text}
            
            INSTRUCCIONES:
            1. Responde dudas sobre envíos, garantías, horarios y ubicación.
            2. NO muestres listas de precios ni productos a menos que el usuario pregunte explícitamente "¿Qué ofertas hay?".
            3. Si piden hablar con alguien: <a href='{link_whatsapp}' target='_blank' class='btn-whatsapp-chat'><i class='bi bi-whatsapp'></i> Hablar por WhatsApp</a>
            4. Si es un reclamo: <a href='{link_reclamos}' class='text-danger fw-bold'>Formulario de Reclamos</a>
            
            RESTRICCIONES: {restrictions}
            """

        messages_payload = [{"role": "system", "content": system_prompt}] + history_messages

        # 6. LLAMADA OPENAI
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_payload,
                temperature=0.6,
                max_tokens=350
            )
            bot_response = completion.choices[0].message.content
        except Exception as e:
            print(f"Error OpenAI: {e}")
            bot_response = "Estoy reconectando mis servicios. Intenta en un momento. 🔌"

        # 7. GUARDAR RESPUESTA
        ChatMessage.objects.create(
            user=user,
            session_id=session_id if not user else None,
            role='assistant',
            content=bot_response
        )

        return JsonResponse({'response': bot_response})
    
    return JsonResponse({'error': 'Error'}, status=400)