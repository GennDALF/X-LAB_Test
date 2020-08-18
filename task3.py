#====================================================================#
#   API для доступа к веб-сервису преобразования голос-текст (STT)   #
#====================================================================#

# подключение библиотек для работы с XML, HTTP, генерации уникальных идентификаторов и конфиг-файла 
import xml.etree.ElementTree as XmlElementTree
import httplib2
import uuid
from config import ***

# переменные из конфиг-файла
***_HOST = '***'
***_PATH = '/***_xml'
CHUNK_SIZE = 1024 ** 2


# метод для отправки файла записи голоса на STT преобразование
def speech_to_text(filename=None, bytes=None, request_id=uuid.uuid4().hex, topic='notes', lang='ru-RU', key=***_API_KEY):
	# можно указать путь к файлу либо передать в качестве аргумента собственно файл
    if filename:
		with open(filename, 'br') as file:
			bytes = file.read()
	if not bytes:
		raise Exception('Neither file name nor bytes provided.')
	
    # кодирование в формат PCM (разрядность 16 бит, частота сэмплирования 16 кГц)
	bytes = convert_to_pcm16b16000r(in_bytes=bytes)
	
    # формирование тела запроса
	url = ***_PATH + '?uuid=%s&key=%s&topic=%s&lang=%s' % (
		request_id,
		key,
		topic,
		lang
	)
	
    # разбиение файла на части (требование веб-сервиса?)
	chunks = read_chunks(CHUNK_SIZE, bytes)
    
	# создание объекта для работы с HTTP
	connection = httplib2.HTTPConnectionWithTimeout(***_HOST)
	
    # установление соединения
	connection.connect()
    # тип и адрес HTTP запроса
	connection.putrequest('POST', url)
    # указание на передачу файла по частям
	connection.putheader('Transfer-Encoding', 'chunked')
    # указание на тип файла
	connection.putheader('Content-Type', 'audio/x-pcm;bit=16;rate=16000')
	connection.endheaders()
	
    # передача файла по частям
	for chunk in chunks:
        # подзаголовок из размера отправляемого блока
		connection.send(('%s\r\n' % hex(len(chunk))[2:]).encode())
        # блок
		connection.send(chunk)
        # конец блока
		connection.send('\r\n'.encode())
	
    # конец передачи
	connection.send('0\r\n\r\n'.encode())
    # запрос ответа
	response = connection.getresponse()
	
    # если кот ответа ОК
	if response.code == 200:
		# чтение ответа в строку
        response_text = response.read()
        # из строки в объект XML
		xml = XmlElementTree.fromstring(response_text)
		
        # если STT преобразование прошло успешно
		if int(xml.attrib['success']) == 1:
            # установка нижней границы сравнения (-Inf)
			max_confidence = - float("inf")
			text = ''
			
            # перебор подразделов XML объекта
			for child in xml:
                # поиск текстового блока с максимальным параметром 'confidence',
                # соответствующим, как я понимаю, наиболее вероятному результату STT преобразования
				if float(child.attrib['confidence']) > max_confidence:
					text = child.text
					max_confidence = float(child.attrib['confidence'])
            
			# если нашли текст
			if max_confidence != - float("inf"):
				return text
            # не нашли текст
			else:
				raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
		# ошибка STT преобразования
        else:
			raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
	# код ответа отличается от ОК
    else:
		raise SpeechException('Unknown error.\nCode: %s\n\n%s' % (response.code, response.read()))
	

# своё исключение, наследуемое от Exception
сlass SpeechException(Exception):
	pass
