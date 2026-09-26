# =====================================================================
#  TP07 - Inteligencia Artificial
#  Agente que interpreta comandos en lenguaje natural
#
#  ESTE ES EL ARCHIVO DONDE ESCRIBIS TU PROGRAMA.
#
#  Antes de ejecutarlo:
#    1. Abri INICIAR_SIMULADOR (elegi G1 o Go2)
#    2. Espera a que aparezca la ventana con el robot
#    3. Recien ahi ejecuta este archivo
#
#  Nombre y apellido:  .....................................
#  Comision:           .....................................
#
#  FUNCIONALIDAD AGREGADA: ORDENES COMPUESTAS ("RUTINA DE VISITA")
#  ----------------------------------------------------------------
#  El agente entiende varias ordenes en una sola frase, unidas por
#  comas, "y", "despues", "luego" o "entonces". Por ejemplo, la rutina
#  que fusiona "Presentacion a la clase" + "Ida y vuelta":
#
#    "saluda a los estudiantes, gira 90 grados a la derecha, hace un
#     saludo, avanza 2 metros, media vuelta y para todo"
#
#  Cada paso es un caso ya validado del JSON (#3, #4, #22, #1, #15, #13).
#  Reglas de seguridad de la secuencia:
#    1. Se valida TODA la secuencia ANTES de mover nada. Si un solo paso
#       es peligroso, se bloquea la secuencia entera.
#    2. Si un paso no se entiende, no se ejecuta ninguno (no se adivina).
#    3. Se chequea la bateria antes de arrancar.
#    4. Maximo MAX_PASOS pasos por orden.
# =====================================================================

import re
import unicodedata

from robot import Robot

from ejecutor import Ejecutor
from evaluar import evaluar

# Pone tu nombre: aparece en el reporte que entregas.
ALUMNO = "Apellido, Nombre"


def normalizar(texto):
    """Minusculas, sin tildes y sin signos. 'Girá 90°!' -> 'gira 90 grados'."""
    texto = texto.lower().replace("°", " grados ")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[¿?¡!]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


# =====================================================================
#  ETAPA 1 - CLASIFICADOR DE INTENCION
# =====================================================================
class ClasificadorIntencion:
    """Decide QUE quiere el usuario, sin mirar los numeros todavia."""

    TIPOS = ("MOVER", "GIRAR", "DETENERSE", "SALUDO",
             "CONSULTAR_ESTADO", "DESCONOCIDO")

    # Reglas en orden de prioridad: la primera que coincide gana.
    # DETENERSE va primero para que "no avances" no caiga en MOVER.
    REGLAS = (
        ("DETENERSE", r"\b(deten\w*|pare|frena\w*|quiet\w*|stop|no avances|no te muevas|no camines)\b"
                      r"|\bpara\b(?!\s+(?:atras|adelante|la|el|los|las|aca|alla|donde))"),
        ("CONSULTAR_ESTADO", r"\b(bateria|carga|estado|como estas)\b"),
        ("SALUDO", r"\b(salud\w*)\b"),
        ("GIRAR", r"\b(gira\w*|gires|rota\w*|voltea\w*|media vuelta|vuelta)\b"),
        ("MOVER", r"\b(avanz\w*|avances|movete|muevete|mueve\w*|camina\w*|anda|adelante|"
                  r"retroced\w*|atras|desplaza\w*)\b"),
    )

    def __init__(self):
        self.modelo = None
        # from entrenar import entrenar_desde_csv
        # self.modelo = entrenar_desde_csv()

    def clasificar(self, texto):
        """Devuelve uno de los seis tipos de TIPOS."""
        if self.modelo is not None:
            try:
                return self.modelo.predict([texto])[0]
            except Exception:
                pass            # si el modelo falla, siguen las reglas

        t = normalizar(texto)
        for tipo, patron in self.REGLAS:
            if re.search(patron, t):
                return tipo
        return "DESCONOCIDO"


# =====================================================================
#  ETAPA 2 - EXTRACTOR DE PARAMETROS
# =====================================================================
class ExtractorParametros:
    """Saca los numeros del texto. Sigue en unidades humanas."""

    NUM = r"(\d+(?:[.,]\d+)?)"

    def __init__(self, velocidad_max=0.20):
        self.velocidad_max = velocidad_max

    def _num(self, s):
        return float(s.replace(",", "."))

    def extraer(self, texto, tipo):
        t = normalizar(texto)
        p = {}

        # Velocidad explicita: "a 0.2 m/s" (va primero para que el "m" de
        # "m/s" no se confunda con metros)
        m = re.search(self.NUM + r"\s*(m/s|metros por segundo)", t)
        if m:
            p["velocidad_ms"] = self._num(m.group(1))
            t_sin_vel = t[:m.start()] + t[m.end():]
        else:
            t_sin_vel = t

        # Distancia: "2 metros", "1 metro", "50 cm"
        m = re.search(self.NUM + r"\s*(metros?|mts?|m)\b", t_sin_vel)
        if m:
            p["distancia_m"] = self._num(m.group(1))
        else:
            m = re.search(self.NUM + r"\s*(centimetros?|cm)\b", t_sin_vel)
            if m:
                p["distancia_m"] = self._num(m.group(1)) / 100

        # Angulo: "90 grados", "45 grados" (el ° ya se normalizo)
        m = re.search(self.NUM + r"\s*grados?\b", t)
        if m:
            p["angulo_deg"] = self._num(m.group(1))
        elif "media vuelta" in t:
            p["angulo_deg"] = 180.0
        elif re.search(r"\bvuelta (entera|completa)\b", t):
            p["angulo_deg"] = 360.0

        # Direccion
        if re.search(r"\bderecha\b", t):
            p["direccion"] = "derecha"
        elif re.search(r"\bizquierda\b", t):
            p["direccion"] = "izquierda"
        elif re.search(r"\b(atras|retroced\w*)\b", t):
            p["direccion"] = "atras"

        # Adverbios sin numero
        if "velocidad_ms" not in p:
            if re.search(r"\b(despacio|lento|lentamente|suave)\b", t):
                p["velocidad_ms"] = 0.2
            elif re.search(r"\b(rapido|veloz|ligero)\b", t):
                p["velocidad_ms"] = self.velocidad_max   # la maxima permitida
        if "distancia_m" not in p and re.search(r"\bun poco\b", t):
            p["distancia_m"] = 0.3

        # Solo devolvemos lo que tiene sentido para cada tipo
        if tipo == "MOVER":
            p.pop("angulo_deg", None)
        elif tipo == "GIRAR":
            p.pop("distancia_m", None)
            p.pop("velocidad_ms", None)
        elif tipo in ("DETENERSE", "SALUDO", "CONSULTAR_ESTADO"):
            p = {}
        return p


# =====================================================================
#  ETAPA 3 - VALIDADOR DE SEGURIDAD
# =====================================================================
class ValidadorSeguridad:
    """La ultima barrera antes del robot. Componente SEPARADO del clasificador."""

    # Se comparan contra el texto normalizado (sin tildes), por palabra.
    PALABRAS_PELIGROSAS = ("salta", "saltar", "salto", "corre", "correr",
                           "corriendo", "sprint", "empuja", "empujar",
                           "golpea", "golpear", "patea", "rompe", "tira",
                           "tirate", "cae", "caete", "fuerza", "trepa",
                           "sube", "subite", "lanza", "choca")

    DISTANCIA_MAX_M = 5.0     # en un aula, mas que esto no tiene sentido
    ANGULO_MAX_DEG = 180.0

    def __init__(self, perfil):
        self.perfil = perfil

    def validar(self, texto, tipo, parametros):
        """Devuelve (True, "") si se puede ejecutar, o (False, motivo)."""
        t = normalizar(texto)

        # 1. Palabras peligrosas en el TEXTO ORIGINAL, sea cual sea el tipo
        for palabra in self.PALABRAS_PELIGROSAS:
            if re.search(rf"\b{palabra}\b", t):
                return False, f"palabra peligrosa: '{palabra}'"

        p = parametros or {}

        # 2. Velocidad
        v = p.get("velocidad_ms")
        if v is not None and abs(v) > self.perfil.velocidad_max:
            return False, (f"velocidad {v:g} m/s supera el maximo "
                           f"de {self.perfil.velocidad_max:g} m/s")

        # 3. Distancia
        d = p.get("distancia_m")
        if d is not None:
            if d <= 0:
                return False, "distancia invalida"
            if d > self.DISTANCIA_MAX_M:
                return False, (f"distancia {d:g} m supera el maximo "
                               f"de {self.DISTANCIA_MAX_M:g} m")

        # 4. Angulo
        a = p.get("angulo_deg")
        if a is not None and abs(a) > self.ANGULO_MAX_DEG:
            return False, f"angulo {a:g} grados supera el maximo de 180"

        return True, ""

    def validar_bateria(self, bateria):
        if bateria is not None and bateria < self.perfil.bateria_min:
            return False, (f"bateria {bateria} % por debajo del minimo "
                           f"de {self.perfil.bateria_min} %")
        return True, ""


# =====================================================================
#  NUEVO - DIVISOR DE ORDENES COMPUESTAS
# =====================================================================
class DivisorOrdenes:
    """Parte una frase en pasos: 'gira 45 grados y despues avanza'.

    Es una etapa independiente mas, ANTES del clasificador. No sabe nada
    de robots: solo corta texto. Cada paso despues recorre el pipeline
    normal (clasificar -> extraer -> validar).
    """

    # Coma que NO sea decimal ("0,5 metros"), o conectores de secuencia.
    SEPARADOR = re.compile(
        r"(?<!\d),(?!\d)"
        r"|;"
        r"|\by\s+(?:despues|luego|entonces)\b"
        r"|\b(?:despues|luego|entonces)\b"
        r"|\by\b"
    )

    def dividir(self, texto):
        t = normalizar(texto)
        pasos = [p.strip(" .") for p in self.SEPARADOR.split(t)]
        return [p for p in pasos if p]


# =====================================================================
#  EL AGENTE - une las etapas y llama al ejecutor
# =====================================================================
class AgenteRobot:
    MAX_PASOS = 8

    def __init__(self, robot=None):
        self.robot = robot
        perfil = robot.perfil if robot else _perfil_por_defecto()
        self.divisor = DivisorOrdenes()
        self.clasificador = ClasificadorIntencion()
        self.extractor = ExtractorParametros(perfil.velocidad_max)
        self.validador = ValidadorSeguridad(perfil)
        self.ejecutor = Ejecutor(robot) if robot else None
        self.historial = []

    # ---------- analisis de un paso (sin ejecutar) ----------
    def _analizar(self, texto):
        tipo = self.clasificador.clasificar(texto)
        params = self.extractor.extraer(texto, tipo)
        ok, motivo = self.validador.validar(texto, tipo, params)
        return {"texto": texto, "tipo": tipo, "parametros": params,
                "ok": ok, "motivo": motivo}

    def _respuesta(self, texto, tipo, params, ejecutar, bloqueado,
                   confianza, mensaje, pasos=None):
        r = {"tipo": tipo, "parametros": params, "ejecutar": ejecutar,
             "bloqueado": bloqueado, "confianza": confianza,
             "texto_original": texto, "mensaje": mensaje}
        if pasos is not None:
            r["pasos"] = pasos
        self.historial.append(r)
        return r

    def procesar(self, texto):
        """El pipeline completo: dividir -> clasificar -> extraer -> validar -> ejecutar."""

        # 0. El validador mira SIEMPRE la frase completa primero: una palabra
        #    peligrosa en cualquier parte bloquea todo.
        ok, motivo = self.validador.validar(texto, "DESCONOCIDO", {})
        if not ok:
            tipo = self.clasificador.clasificar(texto)
            return self._respuesta(texto, tipo, {}, False, True, 1.0,
                                   f"BLOQUEADO: {motivo}")

        partes = self.divisor.dividir(texto) or [texto]
        if len(partes) > self.MAX_PASOS:
            return self._respuesta(texto, "DESCONOCIDO", {}, False, True, 1.0,
                                   f"BLOQUEADO: mas de {self.MAX_PASOS} pasos en una orden")

        # 1-3. Analizar TODOS los pasos antes de mover nada
        pasos = [self._analizar(p) for p in partes]

        # Si hay varias partes y algunas son DESCONOCIDO pero otras no,
        # puede ser que la "y" no separara ordenes (p. ej. "hola y chau").
        # Si ninguna se entiende, es DESCONOCIDO a secas.
        conocidos = [p for p in pasos if p["tipo"] != "DESCONOCIDO"]
        bloqueados = [p for p in pasos if not p["ok"]]

        if bloqueados:
            b = bloqueados[0]
            msg = (f"BLOQUEADO: {b['motivo']}" if len(pasos) == 1 else
                   f"BLOQUEADO toda la secuencia: el paso '{b['texto']}' - {b['motivo']}")
            return self._respuesta(texto, pasos[0]["tipo"], b["parametros"],
                                   False, True, 1.0, msg, pasos)

        if not conocidos:
            return self._respuesta(texto, "DESCONOCIDO", {}, False, False, 0.3,
                                   "no entendi la orden", pasos)

        desconocidos = [p for p in pasos if p["tipo"] == "DESCONOCIDO"]
        if desconocidos:
            return self._respuesta(
                texto, "DESCONOCIDO", {}, False, False, 0.4,
                f"no entendi el paso '{desconocidos[0]['texto']}': no ejecuto nada",
                pasos)

        # Bateria: se chequea una sola vez, antes de arrancar
        if self.robot is not None:
            try:
                bateria = self.robot.verificar_estado().bateria
            except Exception:
                bateria = None
            ok, motivo = self.validador.validar_bateria(bateria)
            if not ok:
                return self._respuesta(texto, pasos[0]["tipo"], {}, False, True,
                                       1.0, f"BLOQUEADO: {motivo}", pasos)

        # 4. Ejecutar
        resultados = []
        for i, p in enumerate(pasos, 1):
            if self.ejecutor is not None:
                if len(pasos) > 1:
                    print(f"      [SECUENCIA] paso {i}/{len(pasos)}: {p['texto']}")
                resultados.append(self.ejecutor.ejecutar(p["tipo"], p["parametros"]))
            else:
                resultados.append(f"{p['tipo']} {p['parametros']}")

        if len(pasos) == 1:
            mensaje = resultados[0]
        else:
            mensaje = f"secuencia de {len(pasos)} pasos: " + " | ".join(resultados)
        return self._respuesta(texto, pasos[0]["tipo"], pasos[0]["parametros"],
                               True, False, 0.9, mensaje,
                               pasos if len(pasos) > 1 else None)


def _perfil_por_defecto():
    """Permite evaluar el agente sin abrir el simulador."""
    import sys
    from pathlib import Path
    entorno = Path(__file__).resolve().parent.parent / "entorno"
    if str(entorno) not in sys.path:
        sys.path.insert(0, str(entorno))
    from sim.safety import perfil
    return perfil("tp07")


# =====================================================================
#  PROGRAMA PRINCIPAL - no hace falta que lo toques
# =====================================================================
def main():
    import sys

    sin_robot = "--sin-robot" in sys.argv
    # Por defecto los 25 casos se evaluan SIN mover el robot: en el aula no
    # hay lugar para que camine todos los casos seguidos. El robot solo se
    # mueve con las ordenes que se escriben a mano despues.
    # Para el comportamiento anterior (el robot ejecuta los 25 casos):
    #     python mi_desarrollo/mi_tp07.py --evaluar-con-robot
    evaluar_con_robot = "--evaluar-con-robot" in sys.argv

    robot = None
    if not sin_robot:
        robot = Robot()
        robot.conectar()

    try:
        agente = AgenteRobot(robot)
        if robot is not None and not evaluar_con_robot:
            print("\n  Evaluando los 25 casos SIN mover el robot"
                  " (usa --evaluar-con-robot para que los ejecute).")
            evaluar(AgenteRobot(None))
        else:
            evaluar(agente)

        if robot is not None:
            print("\n  Escribi ordenes para el robot. Enter vacio para salir.")
            print("  Proba la rutina: saluda a los estudiantes, gira 90 grados a la derecha,"
                  " hace un saludo, avanza 2 metros, media vuelta y para todo")
            while True:
                try:
                    texto = input("\n  > ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if not texto:
                    break
                r = agente.procesar(texto)
                print(f"    {r['tipo']}  {r.get('mensaje', '')}")
    finally:
        if robot is not None:
            robot.detenerse()
            robot.desconectar()


if __name__ == "__main__":
    main()
