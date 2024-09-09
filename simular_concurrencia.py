import concurrent.futures
import requests
import random

# URL del servidor SOAP en PHP
URL = "http://localhost:8000/soap4/server.php"

# Función para ejecutar una transacción (depositar)
def ejecutar_deposito(cuenta_id, monto, token):
    # Generar el cuerpo de la solicitud SOAP
    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:PersonService">
       <soapenv:Header/>
       <soapenv:Body>
          <urn:depositar>
             <cuenta_id>{cuenta_id}</cuenta_id>
             <monto>{monto}</monto>
             <token>{token}</token>
          </urn:depositar>
       </soapenv:Body>
    </soapenv:Envelope>
    """

    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'urn:PersonService#depositar'
    }

    # Enviar la solicitud SOAP al servidor PHP
    response = requests.post(URL, data=soap_body, headers=headers)

    # Imprimir el contenido de la respuesta para depurar
    print(f"Respuesta completa: {response.content.decode('utf-8')}")

    if response.status_code == 200:
        return f"Depósito exitoso en cuenta {cuenta_id}: {response.content.decode('utf-8')}"
    else:
        return f"Error en depósito para cuenta {cuenta_id}: {response.status_code}"

# Función para simular múltiples depósitos concurrentes en varias cuentas
def simular_concurrencia(num_hilos):
    cuentas = [1, 2, 3, 4]  # Lista de cuentas disponibles
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_hilos) as executor:
        futuros = []
        for i in range(num_hilos):
            cuenta_id = random.choice(cuentas)  # Seleccionar aleatoriamente una cuenta
            monto = random.randint(10, 100)  # Monto aleatorio entre 10 y 100
            token = 'token' + str(i) + str(random.randint(1000, 99999999))  # Token único para cada transacción

            # Ejecutar el depósito en un hilo
            futuros.append(executor.submit(ejecutar_deposito, cuenta_id, monto, token))

        # Obtener los resultados de cada hilo
        for future in concurrent.futures.as_completed(futuros):
            print(future.result())

# Ejecutar la simulación con 9 hilos (3 depósitos por cuenta)
if __name__ == "__main__":
    simular_concurrencia(9)
