import concurrent.futures
import requests
import random
import time
import xml.etree.ElementTree as ET

# URL del servidor SOAP en PHP
URL = "http://localhost:8000/soap4/server.php"

# Espacios de nombres usados en el XML
NAMESPACES = {
    'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
    'ns1': 'urn:PersonService',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'ns2': 'http://xml.apache.org/xml-soap',
    'SOAP-ENC': 'http://schemas.xmlsoap.org/soap/encoding/',
    'xsd': 'http://www.w3.org/2001/XMLSchema'
}

# Función para obtener la información de las cuentas desde la respuesta SOAP
def obtener_info_cuentas():
    soap_body = """
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:PersonService">
       <soapenv:Header/>
       <soapenv:Body>
          <urn:getCuentasInfo/>
       </soapenv:Body>
    </soapenv:Envelope>
    """
    
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'urn:PersonService#getCuentasInfo'
    }
    
    response = requests.post(URL, data=soap_body, headers=headers)
    
    if response.status_code == 200:
        # Procesar la respuesta SOAP como XML
        root = ET.fromstring(response.content)

        cuentas_info = {
            'cuentas': [],
            'maxCuenta': None,
            'minCuenta': None
        }

        # Encontrar el elemento <return>
        return_element = root.find('.//ns1:getCuentasInfoResponse/return', NAMESPACES)
        
        # Iterar sobre los elementos <item> dentro de <return>
        for item in return_element.findall('item', NAMESPACES):
            key = item.find('key', NAMESPACES).text
            value = item.find('value', NAMESPACES)
            
            if key == 'cuentas':
                # Procesar las cuentas
                for cuenta_item in value.findall('item', NAMESPACES):
                    cuenta = {}
                    for cuenta_detail in cuenta_item.findall('item', NAMESPACES):
                        cuenta_key = cuenta_detail.find('key', NAMESPACES).text
                        cuenta_value = cuenta_detail.find('value', NAMESPACES).text
                        cuenta[cuenta_key] = cuenta_value
                    cuentas_info['cuentas'].append({'id': int(cuenta['id']), 'saldo': float(cuenta['saldo'])})
            
            elif key == 'maxCuenta':
                cuenta = {}
                for cuenta_detail in value.findall('item', NAMESPACES):
                    cuenta_key = cuenta_detail.find('key', NAMESPACES).text
                    cuenta_value = cuenta_detail.find('value', NAMESPACES).text
                    cuenta[cuenta_key] = cuenta_value
                cuentas_info['maxCuenta'] = {'id': int(cuenta['id']), 'saldo': float(cuenta['saldo'])}
            
            elif key == 'minCuenta':
                cuenta = {}
                for cuenta_detail in value.findall('item', NAMESPACES):
                    cuenta_key = cuenta_detail.find('key', NAMESPACES).text
                    cuenta_value = cuenta_detail.find('value', NAMESPACES).text
                    cuenta[cuenta_key] = cuenta_value
                cuentas_info['minCuenta'] = {'id': int(cuenta['id']), 'saldo': float(cuenta['saldo'])}

        # Validar si maxCuenta y minCuenta se obtuvieron correctamente
        if cuentas_info['maxCuenta'] is None or cuentas_info['minCuenta'] is None:
            raise Exception("No se pudo obtener la cuenta con saldo máximo o mínimo del servidor.")
        
        return cuentas_info
    else:
        raise Exception(f"Error obteniendo cuentas: {response.status_code}")

# Función para ejecutar una transacción (depositar o retirar)
def ejecutar_transaccion(cuenta_id, monto, token, tipo="depositar"):
    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:PersonService">
       <soapenv:Header/>
       <soapenv:Body>
          <urn:{tipo}>
             <cuenta_id>{cuenta_id}</cuenta_id>
             <monto>{monto}</monto>
             <token>{token}</token>
          </urn:{tipo}>
       </soapenv:Body>
    </soapenv:Envelope>
    """
    
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': f'urn:PersonService#{tipo}'
    }

    response = requests.post(URL, data=soap_body, headers=headers)

    if response.status_code == 200:
        return f"{tipo.capitalize()} exitoso en cuenta {cuenta_id}: {response.content.decode('utf-8')}"
    else:
        return f"Error en {tipo} para cuenta {cuenta_id}: {response.status_code}"

# Función para simular múltiples transacciones concurrentes
def simular_concurrencia(num_hilos, cuentas_info):
    cuentas = [cuenta['id'] for cuenta in cuentas_info['cuentas']]
    max_saldo = cuentas_info['maxCuenta']['saldo']
    min_saldo = cuentas_info['minCuenta']['saldo']
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_hilos) as executor:
        futuros = []
        for i in range(num_hilos):
            cuenta_id = random.choice(cuentas)  # Seleccionar aleatoriamente una cuenta
            tipo_transaccion = random.choice(["depositar", "retirar"])  # Aleatorio entre depositar y retirar
            
            # Límite para retiros o depósitos según el saldo máximo/mínimo
            if tipo_transaccion == "retirar":
                monto = random.uniform(1, min_saldo)  # No más que el saldo mínimo disponible
            else:
                monto = random.uniform(10, max_saldo)  # No más que el saldo máximo

            token = 'token' + str(i) + str(random.randint(1000, 99999999))  # Token único

            # Ejecutar la transacción (depositar o retirar) en un hilo
            futuros.append(executor.submit(ejecutar_transaccion, cuenta_id, monto, token, tipo_transaccion))

        # Obtener los resultados de cada hilo
        for future in concurrent.futures.as_completed(futuros):
            print(future.result())

# Bucle continuo para simular transacciones
if __name__ == "__main__":
    while True:
        try:
            # Obtener la información actualizada de las cuentas
            cuentas_info = obtener_info_cuentas()

            # Ejecutar la simulación con 9 hilos concurrentes
            simular_concurrencia(9, cuentas_info)

            # Esperar 5 segundos antes de repetir el ciclo
            time.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            break
