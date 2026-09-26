# =====================================================================
#  Prueba de la funcionalidad agregada: ORDENES COMPUESTAS
#
#  Corre el caso de casos_rutina.json (id 26, la rutina de visita) con el mismo
#  criterio que evaluar.py, y muestra paso por paso como se dividio
#  cada orden.
#
#    python mi_desarrollo/probar_rutina.py --sin-robot   (sin simulador)
#    python mi_desarrollo/probar_rutina.py               (con el G1 en MuJoCo)
# =====================================================================
import json
import sys
from pathlib import Path

import evaluar
from mi_tp07 import AgenteRobot
from robot import Robot

CASOS_RUTINA = Path(__file__).resolve().parent / "casos_rutina.json"


def main():
    sin_robot = "--sin-robot" in sys.argv
    robot = None
    if not sin_robot:
        robot = Robot()
        robot.conectar()
    try:
        agente = AgenteRobot(robot)
        evaluar.CASOS = CASOS_RUTINA          # mismo evaluador, otros casos
        resumen = evaluar.evaluar(agente)

        print("\n  DETALLE DE LA DIVISION EN PASOS")
        casos = json.loads(CASOS_RUTINA.read_text(encoding="utf-8"))
        for caso in casos:
            r = [h for h in agente.historial if h["texto_original"] == caso["texto"]][-1]
            print(f"\n  #{caso['id']} {caso['texto']}")
            for i, p in enumerate(r.get("pasos") or [], 1):
                marca = "ok " if p["ok"] else "NO "
                print(f"     {i}. [{marca}] {p['tipo']:<17} {p['parametros']}  <- '{p['texto']}'")
            esperados = caso.get("pasos_esperados")
            if esperados:
                obtenidos = [p["tipo"] for p in r.get("pasos") or []]
                estado = "ok" if obtenidos == esperados else f"MAL, esperaba {esperados}"
                print(f"     intenciones de los pasos: {estado}")
            print(f"     -> {r['mensaje']}")
        return 0 if resumen["aciertos"] == resumen["casos"] else 1
    finally:
        if robot is not None:
            robot.detenerse()
            robot.desconectar()


if __name__ == "__main__":
    sys.exit(main())
