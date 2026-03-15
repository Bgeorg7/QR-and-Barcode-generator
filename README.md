#ENGLISH

# Automated Credential Generation and Access Control System

## Project Description
This project was developed to solve a real-world logistical challenge: accreditation and secure access control for over 800 attendees at a major university event. 

The system automates the mass generation of credentials (QR Codes and Code128 Barcodes) from a CSV database. It features dynamic routing, automatically organizing the generated credential files into specific folders based on the attendee's campus or headquarters. Additionally, it includes a real-time access control script designed to interface seamlessly with laser barcode scanners at the event's entry points.

## Key Features
* **Mass Generation & Dynamic Routing:** Reads tabular data (CSV) and generates hundreds of QR/Barcodes in seconds, applying strict naming conventions and automatically sorting them into designated campus folders.
* **Real-Time Attendance Tracking:** A clean, terminal-based interface that logs the exact entry time of each attendee and instantly updates the database to prevent data loss in case of power outages.
* **Anti-Infiltration Security Filter:** Implements keystroke timing analysis to differentiate between the ultra-fast input of a hardware laser scanner and a human attempting to type a code manually, thereby blocking fraudulent access attempts.
* **Double-Entry Validation:** Detects and flags potential credential cloning or sharing by validating if a Unique Identifier (UUID) has already been registered in the system.

## Tech Stack
* **Language:** Python 3.x
* **Data Manipulation:** `pandas`
* **Image Generation:** `qrcode`, `python-barcode`, `Pillow`
* **Core Libraries:** `os`, `time`, `msvcrt`, `datetime`

## Project Structure
* `qr_generator.py`: Script for mass generation of QR codes.
* `barcode_generator.py`: Script for mass generation of linear barcodes.
* `access_control.py`: Sentinel system for real-time scanning and registration at the doors.
* `mock_data.csv`: Sample database (fictional data used to protect real user privacy).

## How to Run (Local Setup)
1. Clone this repository.
2. Create a virtual environment and install dependencies: `pip install pandas qrcode[pil] python-barcode`
3. Run `python qr_generator.py` to watch the system build the directory tree and generate the credentials.
4. Run `python access_control.py` and quickly paste a UUID from the CSV to test the scanner simulation and security filters.

#SPANISH

#Sistema Automatizado de Control de Acceso y Credenciales

## Descripción del Proyecto
Este proyecto fue desarrollado para resolver un desafío logístico real: la acreditación y el control de acceso seguro para más de 800 asistentes en un evento de la Universidad Nacional. 

El sistema automatiza la generación de credenciales (Códigos QR y Códigos de Barras Code128) a partir de una base de datos en formato CSV y gestiona el enrutamiento dinámico de los archivos, organizándolos automáticamente en carpetas según la sede de origen de cada asistente. Además, incluye un script de control de acceso en tiempo real diseñado para operar con escáneres láser en las puertas del evento.

## Características Principales (Features)
* **Generación Masiva y Enrutamiento:** Lee datos tabulares (CSV/Excel) y genera cientos de códigos QR/Barras en segundos, nombrando los archivos bajo un estándar estricto y separándolos por sede automáticamente.
* **Control de Asistencia en Tiempo Real:** Interfaz de terminal limpia que registra la hora exacta de ingreso de cada asistente y actualiza la base de datos al instante para evitar pérdidas de información por cortes de energía.
* **Filtro Anti-Infiltración (Seguridad):** Implementa medición de tiempo de pulsación (keystroke timing) para diferenciar entre la lectura ultra-rápida de una pistola escáner y un humano intentando digitar un código a mano, bloqueando accesos fraudulentos.
* **Validación de Doble Ingreso:** Detecta alertas de clonación o préstamo de credenciales si un identificador único (UUID) intenta registrarse más de una vez.

## Tecnologías Utilizadas
* **Lenguaje:** Python 3.x
* **Manipulación de Datos:** Pandas
* **Generación Gráfica:** qrcode, python-barcode, Pillow
* **Librerías del Sistema:** os, time, msvcrt, datetime

## Estructura del Proyecto
* `generador_qr.py`: Script para la generación masiva de Códigos QR.
* `generador_barras.py`: Script para la generación de Códigos de Barras lineales.
* `control_acceso.py`: Sistema centinela para la lectura y registro en puertas.
* `datos_prueba.csv`: Base de datos de ejemplo (datos ficticios para proteger la privacidad).

## Cómo ejecutarlo (Prueba local)
1. Clona este repositorio.
2. Crea un entorno virtual e instala las dependencias: `pip install pandas qrcode[pil] python-barcode`
3. Ejecuta `python generador_qr.py` para ver cómo se construyen las carpetas y credenciales automáticamente.
4. Ejecuta `python control_acceso.py` y pega rápidamente un código del CSV para probar el registro de asistencia.

