# Chatbot v2 — Redirect Estratégico + CI/CD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extender el chatbot "Cory" para que retorne un objeto `accion` cuando encuentra vuelos en vivo o detalle de paquete, y el frontend renderice un botón que redirige al usuario a la pantalla correspondiente con datos pre-cargados.

**Architecture:** El backend detecta qué tool fue llamada en `ejecutar_tool()` y construye un objeto `accion` con `tipo`, `label`, `path` y `params`. El frontend almacena `accion` por mensaje en el historial local y renderiza un botón bajo la burbuja del asistente. Al clic, `router.push` navega con query params que `ResultadosVuelos.vue` y `DetallePaquete.vue` ya leen sin cambios.

**Tech Stack:** Django 4.2, Groq (llama-3.3-70b-versatile), Vue 3 + Vue Router 4, pytest/Django TestCase, Playwright (E2E), GitHub Actions

---

## File Map

### Backend
- **Modify:** `servicios/chatbot.py` — añadir `_build_accion()`, cambiar firma de `ejecutar_tool()` a `(resultado_json, accion)`, inyectar `accion` en `procesar_mensaje()`
- **Modify:** `servicios/tests.py` — tests unitarios para `_build_accion()` y estructura de retorno de `procesar_mensaje()`
- **Create:** `.github/workflows/ci.yml` — pipeline Django: install → lint → test

### Frontend
- **Modify:** `src/components/ChatBot.vue` — historial local con campo `accion`, render botón condicional, handler `irAResultados()`
- **Modify:** `src/services/api.js` — sin cambios en la función (ya retorna `data` completo incluyendo `accion`)
- **Create:** `tests/e2e/chatbot.spec.js` — Playwright E2E: apertura, mensaje, botón redirect
- **Create:** `.github/workflows/ci.yml` — pipeline Vue: install → build → playwright

---

## Task 1: Backend — `_build_accion()` con tests

**Files:**
- Modify: `servicios/chatbot.py`
- Modify: `servicios/tests.py`

- [ ] **Step 1: Escribir el test unitario para `_build_accion`**

En `servicios/tests.py`:

```python
from django.test import TestCase
from .chatbot import _build_accion


class BuildAccionTest(TestCase):

    def test_vuelos_live_retorna_accion_redirect(self):
        accion = _build_accion("buscar_vuelos_live", {
            "origen": "UIO",
            "destino": "MIA",
            "fecha_salida": "2025-08-15",
            "adultos": 2,
        })
        self.assertEqual(accion["tipo"], "redirect_vuelos")
        self.assertEqual(accion["path"], "/vuelos/resultados")
        self.assertEqual(accion["params"]["origin"], "UIO")
        self.assertEqual(accion["params"]["destination"], "MIA")
        self.assertEqual(accion["params"]["date"], "2025-08-15")
        self.assertEqual(accion["params"]["adults"], 2)
        self.assertIn("label", accion)

    def test_detalle_paquete_retorna_accion_redirect(self):
        accion = _build_accion("get_detalle_paquete", {"paquete_id": 42})
        self.assertEqual(accion["tipo"], "redirect_paquete")
        self.assertEqual(accion["path"], "/paquetes/42")
        self.assertEqual(accion["params"], {})
        self.assertIn("label", accion)

    def test_otras_tools_retornan_none(self):
        self.assertIsNone(_build_accion("get_paquetes", {}))
        self.assertIsNone(_build_accion("get_regiones", {}))
        self.assertIsNone(_build_accion("get_vuelos", {"origen": "UIO"}))
        self.assertIsNone(_build_accion("get_aerolineas", {}))

    def test_vuelos_con_fecha_regreso(self):
        accion = _build_accion("buscar_vuelos_live", {
            "origen": "GYE",
            "destino": "MAD",
            "fecha_salida": "2025-09-01",
            "adultos": 1,
            "fecha_regreso": "2025-09-15",
        })
        self.assertEqual(accion["params"]["return_date"], "2025-09-15")
        self.assertEqual(accion["params"]["tipoViaje"], "idaVuelta")

    def test_vuelos_sin_fecha_regreso_tipo_solo_ida(self):
        accion = _build_accion("buscar_vuelos_live", {
            "origen": "UIO",
            "destino": "MIA",
            "fecha_salida": "2025-08-15",
            "adultos": 1,
        })
        self.assertEqual(accion["params"].get("tipoViaje"), "soloIda")
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

```bash
cd "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Backend"
python manage.py test servicios.tests.BuildAccionTest -v 2
```

Esperado: `ImportError: cannot import name '_build_accion'`

- [ ] **Step 3: Implementar `_build_accion()` en `chatbot.py`**

Agregar la función justo antes del bloque `# DISPATCHER` en `servicios/chatbot.py`:

```python
# =====================================================
# BUILDER DE ACCIONES — Redirect al frontend
# =====================================================

def _build_accion(tool_name, tool_args):
    """
    Construye el objeto accion para redirigir al frontend.
    Retorna None si la tool no requiere redirect.
    """
    if tool_name == "buscar_vuelos_live":
        tiene_regreso = bool(tool_args.get("fecha_regreso"))
        params = {
            "origin": tool_args.get("origen", ""),
            "destination": tool_args.get("destino", ""),
            "date": tool_args.get("fecha_salida", ""),
            "adults": tool_args.get("adultos", 1),
            "tipoViaje": "idaVuelta" if tiene_regreso else "soloIda",
        }
        if tiene_regreso:
            params["return_date"] = tool_args["fecha_regreso"]
        return {
            "tipo": "redirect_vuelos",
            "label": "Ver vuelos disponibles",
            "path": "/vuelos/resultados",
            "params": params,
        }

    if tool_name == "get_detalle_paquete":
        paquete_id = tool_args.get("paquete_id", "")
        return {
            "tipo": "redirect_paquete",
            "label": "Ver detalles y reservar",
            "path": f"/paquetes/{paquete_id}",
            "params": {},
        }

    return None
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

```bash
python manage.py test servicios.tests.BuildAccionTest -v 2
```

Esperado: `5 tests passed`

- [ ] **Step 5: Commit**

```bash
cd "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Backend"
git add servicios/chatbot.py servicios/tests.py
git commit -m "feat(chatbot): add _build_accion for redirect strategy"
```

---

## Task 2: Backend — Modificar `ejecutar_tool()` y `procesar_mensaje()`

**Files:**
- Modify: `servicios/chatbot.py`
- Modify: `servicios/tests.py`

- [ ] **Step 1: Escribir tests para la nueva estructura de retorno**

Agregar en `servicios/tests.py`:

```python
from unittest.mock import patch, MagicMock
from .chatbot import ejecutar_tool, procesar_mensaje


class EjecutarToolTest(TestCase):

    def test_retorna_tupla_resultado_y_accion(self):
        resultado_json, accion = ejecutar_tool("get_aerolineas", {})
        self.assertIsInstance(resultado_json, str)
        self.assertIsNone(accion)

    def test_buscar_vuelos_live_retorna_accion(self):
        args = {"origen": "UIO", "destino": "MIA", "fecha_salida": "2025-08-15", "adultos": 1}
        with patch("servicios.chatbot.tool_buscar_vuelos_live", return_value=[]):
            resultado_json, accion = ejecutar_tool("buscar_vuelos_live", args)
        self.assertIsNotNone(accion)
        self.assertEqual(accion["tipo"], "redirect_vuelos")

    def test_get_detalle_paquete_retorna_accion(self):
        with patch("servicios.chatbot.tool_get_detalle_paquete", return_value={"id": 5}):
            resultado_json, accion = ejecutar_tool("get_detalle_paquete", {"paquete_id": 5})
        self.assertIsNotNone(accion)
        self.assertEqual(accion["tipo"], "redirect_paquete")


class ProcesarMensajeRetornaAccionTest(TestCase):

    @patch("servicios.chatbot.get_groq_client")
    def test_respuesta_sin_tools_tiene_accion_none(self, mock_client):
        # Simular respuesta directa sin tool calls
        mock_choice = MagicMock()
        mock_choice.message.tool_calls = None
        mock_choice.message.content = "Hola, soy Cory."
        mock_client.return_value.chat.completions.create.return_value.choices = [mock_choice]

        resultado = procesar_mensaje("Hola")
        self.assertIn("respuesta", resultado)
        self.assertIn("historial", resultado)
        self.assertIn("accion", resultado)
        self.assertIsNone(resultado["accion"])
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

```bash
python manage.py test servicios.tests.EjecutarToolTest servicios.tests.ProcesarMensajeRetornaAccionTest -v 2
```

Esperado: `TypeError` porque `ejecutar_tool` aún retorna un string, no una tupla.

- [ ] **Step 3: Modificar `ejecutar_tool()` para retornar tupla `(resultado_json, accion)`**

Reemplazar la función `ejecutar_tool` completa en `servicios/chatbot.py`:

```python
def ejecutar_tool(tool_name, tool_args):
    """
    Ejecuta la tool y retorna (resultado_json, accion).
    accion es None para tools que no generan redirect.
    """
    try:
        if tool_name == "get_regiones":
            resultado = tool_get_regiones()
        elif tool_name == "get_paquetes":
            resultado = tool_get_paquetes(**tool_args)
        elif tool_name == "get_detalle_paquete":
            resultado = tool_get_detalle_paquete(**tool_args)
        elif tool_name == "get_destinos":
            resultado = tool_get_destinos(**tool_args)
        elif tool_name == "get_vuelos":
            resultado = tool_get_vuelos(**tool_args)
        elif tool_name == "buscar_vuelos_live":
            resultado = tool_buscar_vuelos_live(**tool_args)
        elif tool_name == "get_aerolineas":
            resultado = tool_get_aerolineas()
        else:
            resultado = {"error": f"Tool '{tool_name}' no reconocida"}
    except Exception as e:
        resultado = {"error": f"Error ejecutando '{tool_name}': {str(e)}"}

    accion = _build_accion(tool_name, tool_args)
    return json.dumps(resultado, ensure_ascii=False, default=str), accion
```

- [ ] **Step 4: Modificar `procesar_mensaje()` para recoger `accion` e incluirla en el retorno**

Localizar en `procesar_mensaje()` el bloque `if assistant_message.tool_calls:` y reemplazarlo completo:

```python
    accion_final = None  # Se acumula si alguna tool genera redirect

    # ¿El modelo quiere llamar una tool?
    if assistant_message.tool_calls:
        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        })

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            tool_result, accion = ejecutar_tool(tool_name, tool_args)
            if accion is not None:
                accion_final = accion

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        response2 = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        respuesta_final = response2.choices[0].message.content

    else:
        respuesta_final = assistant_message.content
```

Y al final de `procesar_mensaje()`, cambiar el return:

```python
    historial_actualizado = historial_limitado + [
        {"role": "user", "content": mensaje_usuario},
        {"role": "assistant", "content": respuesta_final}
    ]

    return {
        "respuesta": respuesta_final,
        "historial": historial_actualizado,
        "accion": accion_final,
    }
```

También actualizar el bloque del catálogo vacío al inicio para incluir `accion`:

```python
        return {
            "respuesta": respuesta_vacia,
            "historial": historial_actualizado,
            "accion": None,
        }
```

- [ ] **Step 5: Correr todos los tests del backend**

```bash
python manage.py test servicios -v 2
```

Esperado: todos los tests pasan.

- [ ] **Step 6: Smoke test manual del endpoint**

```bash
curl -s -X POST http://localhost:8000/api/chatbot/ \
  -H "Content-Type: application/json" \
  -d "{\"mensaje\": \"Busca vuelos de UIO a MIA para el 2025-08-15, 1 adulto\"}" | python -m json.tool | grep -A20 "accion"
```

Esperado: campo `"accion"` con `tipo`, `label`, `path`, `params` en la respuesta.

- [ ] **Step 7: Commit**

```bash
git add servicios/chatbot.py servicios/tests.py
git commit -m "feat(chatbot): ejecutar_tool returns (json, accion), procesar_mensaje includes accion in response"
```

---

## Task 3: Frontend — Botón de redirect en `ChatBot.vue`

**Files:**
- Modify: `src/components/ChatBot.vue`

- [ ] **Step 1: Agregar `useRouter` y el handler `irAResultados`**

En el bloque `<script setup>` de `ChatBot.vue`, agregar el import de router y el handler:

```js
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { enviarMensajeChatbot } from '../services/api.js'

const router = useRouter()

// ... (estado existente sin cambios) ...

function irAResultados(accion) {
  router.push({ path: accion.path, query: accion.params })
}
```

- [ ] **Step 2: Cambiar el historial local para soportar campo `accion`**

En `enviarMensaje()`, cambiar la línea donde se agrega la respuesta del asistente:

```js
// ANTES:
historial.value.push({ role: 'assistant', content: resultado.respuesta })

// DESPUÉS:
historial.value.push({
  role: 'assistant',
  content: resultado.respuesta,
  accion: resultado.accion || null,
})
```

- [ ] **Step 3: Agregar el botón de redirect en el template**

Reemplazar el bloque `<!-- Historial de mensajes -->` en el template:

```html
<!-- Historial de mensajes -->
<div
  v-for="(msg, index) in historial"
  :key="index"
  class="mensaje"
  :class="msg.role === 'user' ? 'mensaje-usuario' : 'mensaje-asistente'"
>
  <div class="mensaje-wrapper">
    <div class="mensaje-burbuja" v-html="formatearMensaje(msg.content)"></div>
    <button
      v-if="msg.accion"
      class="chatbot-btn-accion"
      @click="irAResultados(msg.accion)"
    >
      ✈ {{ msg.accion.label }}
    </button>
  </div>
</div>
```

- [ ] **Step 4: Agregar estilos para el botón de acción**

En el bloque `<style scoped>`, agregar al final (antes del cierre del media query):

```css
/* =====================================================
   BOTÓN DE ACCIÓN (redirect)
   ===================================================== */
.mensaje-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 100%;
}

.chatbot-btn-accion {
  align-self: flex-start;
  background: var(--chat-primary);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 7px 14px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.15s;
  font-family: 'Arial', sans-serif;
  white-space: nowrap;
}

.chatbot-btn-accion:hover {
  background: var(--chat-primary-dark);
  transform: scale(1.03);
}
```

- [ ] **Step 5: Verificar en el navegador**

1. Abrir `http://localhost:5173`
2. Abrir el chat (burbuja dorada)
3. Escribir: `"Busca vuelos de UIO a MIA para el 2025-08-15, 1 adulto"`
4. Verificar que aparece la respuesta textual del asistente
5. Verificar que bajo la burbuja aparece el botón "✈ Ver vuelos disponibles"
6. Hacer clic y verificar que navega a `/vuelos/resultados?origin=UIO&destination=MIA&date=2025-08-15&adults=1`

- [ ] **Step 6: Probar también con paquete**

En el chat escribir: `"Dame detalles del paquete Europa Clásica"`
Verificar botón "Ver detalles y reservar" y que navega a `/paquetes/<id>`

- [ ] **Step 7: Commit**

```bash
cd "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Frontend"
git add src/components/ChatBot.vue
git commit -m "feat(chatbot): render redirect button when accion present in assistant response"
```

---

## Task 4: CI/CD — Pipeline Backend (GitHub Actions)

**Files:**
- Create: `.github/workflows/ci.yml` (en `Proyecto_CorpoDG_Backend`)

- [ ] **Step 1: Crear el directorio y el workflow**

```bash
mkdir -p "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Backend\.github\workflows"
```

Crear `.github/workflows/ci.yml`:

```yaml
name: Backend CI

on:
  push:
    branches: [main, develop, feat/reservas, feat/gabriel/chatbot_v2]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: prueba_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      SECRET_KEY: django-insecure-ci-test-key
      DEBUG: "True"
      ALLOWED_HOSTS: localhost,127.0.0.1
      DB_ENGINE: django.db.backends.postgresql
      DB_NAME: prueba_test
      DB_USER: postgres
      DB_PASSWORD: postgres
      DB_HOST: localhost
      DB_PORT: 5432
      GROQ_API_KEY: dummy-key-for-tests
      STRIPE_SECRET_KEY: sk_test_dummy
      STRIPE_PUBLISHABLE_KEY: pk_test_dummy
      STRIPE_WEBHOOK_SECRET: whsec_dummy
      BOOKING_SANDBOX: "1"
      SEATMAP_SANDBOX: "1"
      BOOKING_SEND_EMAIL: "0"
      CLIENT_ID: dummy
      CLIENT_SECRET: dummy
      SABRE_AUTH_URL: https://example.com
      SABRE_TOKEN_REFRESH_MARGIN: "60"
      FRONTEND_BOOKING_SUCCESS_URL: http://localhost:5173/reserva/confirmada
      FRONTEND_BOOKING_CANCEL_URL: http://localhost:5173/reserva/cancelada
      CORS_ALLOWED_ORIGINS: http://localhost:5173
      WHATSAPP_TOKEN: dummy
      WHATSAPP_PHONE_NUMBER_ID: "0"
      WHATSAPP_TEMPLATE_NAME: dummy
      WHATSAPP_TEMPLATE_LANGUAGE: es_EC
      WHATSAPP_RECIPIENT_NUMBER: "0"
      EMAIL_BACKEND: django.core.mail.backends.console.EmailBackend
      XAI_API_KEY: dummy
      XAI_MODEL: llama-3.3-70b-versatile
      XAI_API_BASE_URL: https://api.groq.com/openai/v1

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.13
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Django system check
        run: python manage.py check

      - name: Run migrations
        run: python manage.py migrate --run-syncdb

      - name: Run tests
        run: python manage.py test servicios -v 2
```

- [ ] **Step 2: Commit**

```bash
cd "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Backend"
git add .github/workflows/ci.yml requirements.txt
git commit -m "ci: add GitHub Actions pipeline for Django backend"
```

---

## Task 5: CI/CD — Pipeline Frontend + Playwright E2E

**Files:**
- Create: `.github/workflows/ci.yml` (en `Proyecto_CorpoDG_Frontend`)
- Create: `tests/e2e/chatbot.spec.js`

- [ ] **Step 1: Instalar Playwright**

```bash
cd "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Frontend"
npm install --save-dev @playwright/test
npx playwright install chromium
```

- [ ] **Step 2: Crear `playwright.config.js` en la raíz del frontend**

```js
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60000,
  },
})
```

- [ ] **Step 3: Crear `tests/e2e/chatbot.spec.js`**

```bash
mkdir -p "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Frontend\tests\e2e"
```

```js
import { test, expect } from '@playwright/test'

test.describe('Chatbot Cory', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('burbuja del chat es visible en la página', async ({ page }) => {
    const burbuja = page.locator('.chatbot-burbuja')
    await expect(burbuja).toBeVisible()
  })

  test('abre y cierra el chat al hacer clic en la burbuja', async ({ page }) => {
    const burbuja = page.locator('.chatbot-burbuja')
    const ventana = page.locator('.chatbot-ventana')

    await expect(ventana).not.toBeVisible()
    await burbuja.click()
    await expect(ventana).toBeVisible()
    await burbuja.click()
    await expect(ventana).not.toBeVisible()
  })

  test('muestra mensaje de bienvenida de Cory al abrir', async ({ page }) => {
    await page.locator('.chatbot-burbuja').click()
    const bienvenida = page.locator('.mensaje-asistente').first()
    await expect(bienvenida).toContainText('Cory')
  })

  test('envía un mensaje y recibe respuesta del asistente', async ({ page }) => {
    await page.locator('.chatbot-burbuja').click()

    const input = page.locator('.chatbot-input')
    await input.fill('¿Qué paquetes tienen disponibles?')
    await page.locator('.chatbot-btn-enviar').click()

    // El mensaje del usuario aparece
    const mensajeUsuario = page.locator('.mensaje-usuario').last()
    await expect(mensajeUsuario).toContainText('paquetes')

    // El asistente responde (esperar hasta 20s por la llamada al LLM)
    const mensajeAsistente = page.locator('.mensaje-asistente').last()
    await expect(mensajeAsistente).not.toContainText('Cory', { timeout: 20000 })
    await expect(page.locator('.mensaje-asistente').last()).toBeVisible({ timeout: 20000 })
  })

  test('botón de redirect aparece cuando el chatbot devuelve accion', async ({ page }) => {
    // Mock de la API para simular respuesta con accion
    await page.route('**/api/chatbot/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          respuesta: 'Encontré vuelos de Quito a Miami desde $420.',
          historial: [],
          accion: {
            tipo: 'redirect_vuelos',
            label: 'Ver vuelos disponibles',
            path: '/vuelos/resultados',
            params: { origin: 'UIO', destination: 'MIA', date: '2025-08-15', adults: 1, tipoViaje: 'soloIda' },
          },
        }),
      })
    })

    await page.locator('.chatbot-burbuja').click()
    await page.locator('.chatbot-input').fill('Vuelos de UIO a MIA el 2025-08-15')
    await page.locator('.chatbot-btn-enviar').click()

    const btnAccion = page.locator('.chatbot-btn-accion')
    await expect(btnAccion).toBeVisible({ timeout: 10000 })
    await expect(btnAccion).toContainText('Ver vuelos disponibles')
  })

  test('botón de redirect navega a /vuelos/resultados con query params', async ({ page }) => {
    await page.route('**/api/chatbot/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          respuesta: 'Encontré vuelos.',
          historial: [],
          accion: {
            tipo: 'redirect_vuelos',
            label: 'Ver vuelos disponibles',
            path: '/vuelos/resultados',
            params: { origin: 'UIO', destination: 'MIA', date: '2025-08-15', adults: 1, tipoViaje: 'soloIda' },
          },
        }),
      })
    })

    await page.locator('.chatbot-burbuja').click()
    await page.locator('.chatbot-input').fill('test')
    await page.locator('.chatbot-btn-enviar').click()

    await page.locator('.chatbot-btn-accion').click()

    await expect(page).toHaveURL(/\/vuelos\/resultados/, { timeout: 5000 })
    const url = new URL(page.url())
    expect(url.searchParams.get('origin')).toBe('UIO')
    expect(url.searchParams.get('destination')).toBe('MIA')
  })

})
```

- [ ] **Step 4: Correr los E2E localmente**

```bash
cd "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Frontend"
npx playwright test --reporter=list
```

Esperado: 5/5 tests pasan (el test de LLM real puede tardar ~15s).

- [ ] **Step 5: Crear `.github/workflows/ci.yml` para el frontend**

```bash
mkdir -p "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Frontend\.github\workflows"
```

```yaml
name: Frontend CI

on:
  push:
    branches: [main, develop, feat/reservas, feat/gabriel/chatbot_v2]
  pull_request:
    branches: [main, develop]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Build (verifica que compila sin errores)
        run: npm run build

      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium

      - name: Run E2E tests
        run: npx playwright test --reporter=list
        env:
          CI: true

      - name: Upload Playwright report on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 3
```

- [ ] **Step 6: Commit**

```bash
cd "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Frontend"
git add playwright.config.js tests/e2e/chatbot.spec.js .github/workflows/ci.yml package.json package-lock.json
git commit -m "ci: add Playwright E2E tests and GitHub Actions pipeline for frontend"
```

---

## Task 6: Push y verificación final

- [ ] **Step 1: Push backend**

```bash
cd "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Backend"
git push origin feat/gabriel/chatbot_v2
```

- [ ] **Step 2: Push frontend**

```bash
cd "C:\Users\PC\Desktop\Proyecto Capstone\Proyecto_CorpoDG_Frontend"
git push origin feat/gabriel/chatbot_v2
```

- [ ] **Step 3: Verificar smoke test de integración completa**

```bash
# Test backend con vuelos live
curl -s -X POST http://localhost:8000/api/chatbot/ \
  -H "Content-Type: application/json" \
  -d "{\"mensaje\": \"Busca vuelos de UIO a MIA para el 2025-08-15, 1 adulto\"}" \
  | python -m json.tool
```

Verificar en la respuesta: `"accion"` no es null, `"tipo": "redirect_vuelos"`, `"path": "/vuelos/resultados"`.

- [ ] **Step 4: Verificar flujo visual en el browser**

1. Abrir `http://localhost:5173`
2. Abrir chat → escribir "Busca vuelos de UIO a MIA para el 2025-08-15, 1 adulto"
3. Confirmar botón dorado "✈ Ver vuelos disponibles" bajo la burbuja
4. Clic → confirmar redirección a `/vuelos/resultados` con resultados pre-cargados
5. Volver → abrir chat → "Dame detalles del paquete Europa Clásica"
6. Confirmar botón "Ver detalles y reservar" y navegación a `/paquetes/<id>`

---

## Self-Review

**Spec coverage:**
- ✅ `_build_accion()` para `buscar_vuelos_live` y `get_detalle_paquete`
- ✅ `ejecutar_tool()` retorna tupla
- ✅ `procesar_mensaje()` incluye `accion` en respuesta
- ✅ Frontend renderiza botón cuando `accion` presente
- ✅ `router.push` con `path` y `query: params`
- ✅ `ResultadosVuelos.vue` y `DetallePaquete.vue` sin cambios
- ✅ CI/CD backend: install → check → migrate → test
- ✅ CI/CD frontend: install → build → playwright E2E
- ✅ Trigger en PR y push a main/develop/feat/**

**Firma de tipos consistente:**
- `ejecutar_tool()` → `(str, dict | None)` en Tasks 1 y 2 ✅
- `accion.path` / `accion.params` / `accion.label` usados en Task 3 = definidos en Task 1 ✅
- `.chatbot-btn-accion` definido en Task 3 Step 4 = usado en test Task 5 ✅
