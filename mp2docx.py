""""
Convert MP(xml) to docx
"""


class MpXml2Docx:
    """
    Преобразователь xml межевого  в печатный вид (word)
		
    """
    CNST_FORMAT = 'docx'
    CNST_PATH_TPL = 'template/common/'

    def __init__(self):
        self.name_number = 0
        self.tempfolder = tempfile.mkdtemp()

    def close(self):
        """
        удаление темповой директории

        """
        if os.path.exists(self.tempfolder):
            shutil.rmtree(self.tempfolder)

    def fast_iter_element(self, elem: object, func: object, args: object = [], kwargs: object = {}) -> object:
        """
		the node  cleaning
		
		:param context: context
		:param func: callback - renderToTPL
		:param args: args
		:param kwargs: kwargs
		:return: None
		:rtype: XMLElemet
        """
        func(elem, *args, **kwargs)
        elem.clear()
        while elem.getprevious() is not None:
            if type(elem.getprevious()) == etree._Element:
                if elem.getparent() is not None:
                    del elem.getparent()[0]
            else:
                break

    def render_tpl(self, node, XMLClass, path_tpl, name_result):
        """
        Рендер шаблона

        :param node:  узел- noda
        :param XMLClass: класс отвечающий за парсинг данной ноды в dict (to_dict)
        :param path_tpl: путь до template
        :return: word файл  с наименованием =  [Number - позиция word- элемента в файле]+ [Number - позиция node].docx
        """
        try:
            if len(node) > 0 or node.text:
                tpl = DocxTemplate(path_tpl)
                instance = XMLClass(node)
                tpl.render(instance.to_dict())
                file_res = '.'.join([name_result, self.CNST_FORMAT])
                tpl.save(os.path.join(self.tempfolder, file_res))                
        except Exception as e:
            pass

    def run_render_tpl_node(self, elem, xml_class_name, is_clean, pos_node):
        """
        Запуск парсинга определенного блока xml
		
        :param elem: node
        :param xml_class_name: class -> retun dict
        :param is_clean: очищать  узел или там еще что то нужно
        :param pos_node: просто порядковый номер позици узла
        :return: docx
        """
        dir = os.path.dirname(__file__)
        path_tpl = os.path.normpath(os.path.join(dir,self.CNST_PATH_TPL + BINDER_FILE[elem.tag]['tpl']))
        if is_clean:
            self.fast_iter_element(elem, self.render_tpl, args=(xml_class_name,
                                                                path_tpl,
                                                                BINDER_FILE[elem.tag]['pos_doc'] + str(pos_node)))
        else:
            self.render_tpl(elem, xml_class_name, path_tpl,BINDER_FILE[elem.tag]['pos_doc'] + str(pos_node))

    def __context_parser(self, context):
        """
        Парсим node
        
		:param context:
        """
        i = 0
        try:
            for event, elem in context:
                i += 1
                if elem.tag in BINDER_FILE.keys()  and event == 'end': #пришлось по end, так iterparse может отдать не все
                    if elem.tag == 'SubParcels' and event == 'end' and elem.getparent().tag != 'Package':
                        continue
                    self.run_render_tpl_node(elem, BINDER_FILE[elem.tag]['class'], BINDER_FILE[elem.tag]['clear'], i)
        except Exception as e:
            pass
        finally:
            del context

    def __xml_block_to_docx(self, path):
        """
        Формирование списка док. файлов  по блокам xml
			
        :param path: путь до xml файла
        """
        # get an iterable
        context = iterparse(path, events=("start", "end"))
        context = iter(context)
        self.__context_parser(context)
        del context

    def __element_body_docx(self, path):
        """
        
		:param path: получить блок ворд -файла
        :return: element docx
        """
        # Don't add a page break if you've
        # reached the last file.
        doc = Document(path)
        doc.add_page_break()
        for element in doc.element.body:
            yield element

    def combine_word_documents(self, result_path_file):
        """
        Собираем все файлы в единый документ
        
		:param result_path_file: iterable список файлов
        """
        files = sorted(os.listdir(self.tempfolder))
        _dcx = filter(lambda x: x.endswith('.' + self.CNST_FORMAT), files)
        _dcx = map(lambda x: os.path.join(self.tempfolder, x), _dcx)

        merged_document = Document()
        for filnr, file in enumerate(_dcx):
            _ = os.path.join(file)
            if filnr == 0:
                merged_document = Document(_)
            else:
                for element in self.__element_body_docx(_):
                    merged_document.element.body.append(element)
        merged_document.save(result_path_file)

    def run(self, path_file, result_file):
        """
        run convert xml to  word

        :param path_file:  sourse file xml
        :param result_file:  path file resultc
        """
        self.__xml_block_to_docx(path_file)
        self.combine_word_documents(result_file)

