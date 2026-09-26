# TP07 — Inteligencia Artificial · Humanoide Unitree G1

Agente que interpreta órdenes en lenguaje natural ("avanzá 2 metros", "girá 90 grados a la derecha", "saluda a los estudiantes") y las ejecuta en el robot Unitree G1, simulado en MuJoCo.

## Instalación (una sola vez, Windows)

Doble clic en **`INSTALAR.bat`**. Instala lo que falte:

- Python 3.10+ (al instalarlo a mano, tildar **"Add python.exe to PATH"** y **"py launcher"**)
- Microsoft Visual C++ Redistributable x64 — https://aka.ms/vs/17/release/vc_redist.x64.exe
- `mujoco` y `numpy` (`py -3 -m pip install mujoco numpy`)

Opcional, sólo para la extensión con modelo entrenado: `py -3 -m pip install scikit-learn`.

Detalles y problemas frecuentes: [`INSTALACION.md`](INSTALACION.md).

## Uso

1. **`INICIAR_SIMULADOR.bat`** → elegir `1` (G1). Dejar la ventana abierta.
2. Con el simulador abierto:
   - **`EJECUTAR_MI_CODIGO.bat`** — evalúa los 25 casos **sin mover el robot** y después permite escribir órdenes a mano (Enter vacío para salir). Para que el robot ejecute los 25 casos: `py -3 mi_desarrollo\mi_tp07.py --evaluar-con-robot`.
   - **`PROBAR_RUTINA.bat`** — rutina de visita: saluda, gira 90°, saluda, avanza 2 m, media vuelta y se detiene. Necesita unos 2,5 m libres.

Sin simulador: `py -3 mi_desarrollo\mi_tp07.py --sin-robot`

**Rendimiento:** en notebooks con placa NVIDIA, forzar `python.exe` a usar la GPU dedicada (Configuración → Sistema → Pantalla → Gráficos → Alto rendimiento).

## Estructura

```
mi_desarrollo/     el agente (mi_tp07.py) y los archivos de la cátedra
entorno/sim/       simulador + modelos oficiales de Unitree (licencia BSD-3)
*.bat / *.sh       instalar, iniciar el simulador, ejecutar
```
