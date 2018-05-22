"""
  Сериализция основных блоков мп - xmk
  Основные блоки:
  Титульный лист,
  Исходные данные,
  Средства об измерениях,
  Сведения об обрузуемых зу и их частях,
  Сведения об уточняемом учатске и частях,
  Сведения об измененных учасках и их частях,
  Единое землепользование,
  Сведения о земельных участках, посредством которых обеспечивается доступ,
  Заключение кадастрового инженера
"""
from serialization.basic import *
from utils.xsd import value_from_xsd
from datetime import datetime
import logging
from logging.config import fileConfig
# fileConfig('loggers/logging_config.ini')
logger = logging.getLogger()


class XmlTitleDict:
    """
        Формированяи словаря для титульника
    """
    def __init__(self, node):
        """
        GeneralCadastralWorks
        """
        self.node = node
        self.contractor = None

    def __children_dict(self, node, *args):
        """

        :param node: Contractor/child
        :return: dict (node.tag : node.text)
        """
        res = dict()
        for el in node:
            res[el.tag] = el.text
        return res

    def __contractor(self):
        if not self.contractor:
            return self.__children_dict(self.node.xpath('Contractor/child::*'))
        return self.contractor

    def __xml_reason_to_text(self):
        return ''.join(self.node.xpath('Reason/text()'))

    def __xml_purpose_to_text(self):
        return ''.join(self.node.xpath('Purpose/text()'))

    def __xml_client_to_text(self):
        return ' '.join(self.node.xpath('Clients/*[1]/child::*/node()/text()'))

    def __xml_contrsactor_fio_to_text(self):
        _ = self.__contractor()
        if _:
            return f"{_.get('FamilyName', '')} " \
                   f"{_.get('FirstName', '')} " \
                   f"{_.get('Patronymic', '')}"
        return ''

    def __xml_ncertificate_to_text(self):
        _ = self.__contractor()
        if _:
            return _.get('NCertificate', '')
        return ''

    def __xml_telefon_to_text(self):
        _ = self.__contractor()
        if _:
            return _.get('Telephone', '')
        return ''

    def __xml_email_to_text(self):
        _ = self.__contractor()
        if _:
            return _.get('Email', '')
        return ''

    def __xml_address_to_text(self):
        _ = self.__contractor()
        if _:
            return _.get('Address', '')
        return ''

    def __xml_organization_to_text(self):
        return ' '.join(self.node.xpath('Contractor/Organization/node()/text()'))

    def __xml_data_to_text(self):
        _dt = datetime.strptime(dict(self.node.attrib).get('DateCadastral'), "%Y-%m-%d")
        if _dt:
            return  f"""{_dt:%d.%m.%Y}"""
        return ''

    def to_dict(self):
        """
            Данный  метод  возвращает словарь значения для  заполнения  шаблона title.docx

        :return: dict->cnfg.Title
        """
        result = None
        try:
            value_title = [self.__xml_reason_to_text(), self.__xml_purpose_to_text(),
                           self.__xml_client_to_text(), self.__xml_contrsactor_fio_to_text(),
                           self.__xml_ncertificate_to_text(), self.__xml_telefon_to_text(), self.__xml_address_to_text(),
                           self.__xml_email_to_text(), self.__xml_organization_to_text(), self.__xml_data_to_text()]
            result = dict(zip(cnfg.TITLE.attr, value_title))
        except Exception as e:
            logger.error(f""" Ошибки при формировании титульника {e} """)
        else:
            logger.info(f"""Словарь титульного {result}""")
        return result


class XmlSurveyDict(XMLElemenBase):
    """
        Формирование словаря для  Сведени о выполненных измерениях и расчетах
        :param root: Survey
    """
    pathListGeopointsOpred = 'GeopointsOpred/child::*'
    pathTochAreaParcel = 'TochnAreaParcels/child::*'
    pathTochGeopoitsParcels = 'TochnGeopointsParcels/child::*'

    def __xml_geopoints_opred_to_list(self):
        """
        :return: list (geopoint_opreds)
        """
        el = self.node.xpath(self.pathListGeopointsOpred)
        res = []
        try:
            for index, _ in enumerate(el):
                _method = ''.join(_.xpath('Methods/child::*[name()="GeopointOpred"]/text()'))
                method_val = value_from_xsd('/'.join([cnfg.PATH_XSD,cnfg.GEOPOINTS_OPRED.dict['geopointopred']]),_method)
                res.append([str(index + 1),''.join(_.xpath('CadastralNumberDefinition/text()')), method_val])
        except Exception as e:
            logger.error(f"Ошибка при разборе  {el}")
        finally:
            el.clear
        return res

    def __xml_toch_area_parcel_to_list(self):
        el = self.node.xpath(self.pathTochAreaParcel)
        res = []
        try:
            for index, _ in enumerate(el):
                res.append([str(index + 1),
                            ''.join(_.xpath('CadastralNumberDefinition/text()')),
                            ''.join(_.xpath('Area/Area/text()')),
                            ''.join(_.xpath('Formula/text()')),
                            ])
        finally:
            el.clear()
        return res

    def __xml_toch_geopoints_parcel_to_list(self):
        el = self.node.xpath(self.pathTochGeopoitsParcels)
        res = []
        try:
            for index, _ in enumerate(el):
                res.append([str(index + 1),
                            ''.join(_.xpath('CadastralNumberDefinition/text()')),
                            ''.join(_.xpath('Formula/text()')),
                            ])
        finally:
            el.clear()
        return res

    def to_dict(self):
        _res = None
        try:
            _res = {
                cnfg.GEOPOINTS_OPRED.name: StaticMethod.merge_array_list(cnfg.GEOPOINTS_OPRED.attr,
                                                                    self.__xml_geopoints_opred_to_list()),
                cnfg.TOCHN_GEOPOINTS_PARCELS.name: StaticMethod.merge_array_list(cnfg.TOCHN_GEOPOINTS_PARCELS.attr,
                                                                            self.__xml_toch_geopoints_parcel_to_list()),
                cnfg.TOCHN_AREA_PARCELS.name: StaticMethod.merge_array_list(cnfg.TOCHN_AREA_PARCELS.attr,
                                                                       self.__xml_toch_area_parcel_to_list())
            }
        except Exception as e:
            logger.error(f"""Ошибка в формировании  словаря для средств измерений {e}""")
        else:
            logger.info(f"""Словарь для средст измерений готов {_res}""")
        return _res


class XmlInputDataDict(XMLElemenBase):
    """
        формирование словаря Исхпдные данные
        :param root == InputData
    """
    NAME = 'Name'
    NUMBER = 'Number'
    DATE = 'Date'
    pathListDocuments = 'Documents/child::*'
    pathGeodesicBses = 'GeodesicBases/child::*'
    pathMeansSurveys = 'MeansSurvey/child::*'
    pathObjectsRealty = 'ObjectsRealty/child::*'
    pathListSystemCood= '../CoordSystems/child::*/@Name'

    def __xml_sys_coord_to_text(self):
        return ''.join(self.node.xpath(self.pathListSystemCood))

    def __xml_documents_to_list(self):
        el = self.node.xpath(self.pathListDocuments)
        res = []
        try:
            for index, _ in enumerate(el):
                _dt =  datetime.strptime(''.join(_.xpath('Date/text()')),'%Y-%m-%d').strftime('%d.%m.%Y')
                _tmp = f" № {''.join(_.xpath('Number/text()'))} от { _dt } г."
                _name = ''.join(_.xpath('Name/text()'))
                if not _name:
                    _name = StaticMethod.xml_key_to_text(_, 'CodeDocument/text()', cnfg.INPUT_DATA.dict['alldocuments'])
                res.append([str(index + 1),_name,_tmp])
        finally:
            el.clear()
        return res

    def __xml_geodesic_bases_to_list(self):
        el = self.node.xpath(self.pathGeodesicBses)
        res = []
        try:
            for index, _ in enumerate(el):
                _tmp = f"{''.join(_.xpath('PName/text()'))} {''.join(_.xpath('PKind/text()'))}"
                res.append([str(index + 1), _tmp, ''.join(_.xpath('PKlass/text()')),
                            ''.join(_.xpath('OrdX/text()')),
                            ''.join(_.xpath('OrdY/text()'))])
        finally:
            el.clear()
        return res

    def __xml_means_surveys_to_list(self):
        el = self.node.xpath(self.pathMeansSurveys)
        res = []
        try:
            for index, _ in enumerate(el):
                res.append([str(index + 1), ''.join(_.xpath('Name/text()')),
                            ' '.join(_.xpath('Registration/child::*/text()')),
                            ''.join(_.xpath('CertificateVerification/text()'))])
        finally:
            el.clear()
        return res

    def __xml_objects_realtys_to_list(self):
        el = self.node.xpath(self.pathObjectsRealty)
        res = list()
        try:
            for index, _ in enumerate(el):
                res.append([str(index + 1),''.join(_.xpath('CadastralNumberParcel/text()')), ', '.join(_.xpath('InnerCadastralNumbers/child::*/text()'))])
            logging.info(f"""Сведения о наличии объектов недвижимости { res }""")
        finally:
            el.clear()
        return res

    def to_dict(self):
        _res = None
        try:
            _res = {cnfg.INPUT_DATA.name: StaticMethod.merge_array_list(cnfg.INPUT_DATA.attr, self.__xml_documents_to_list()),
                    cnfg.SYSTEM_COORD: self.__xml_sys_coord_to_text(),
                    cnfg.GEODESIC_BASES.name: StaticMethod.merge_array_list(cnfg.GEODESIC_BASES.attr, self.__xml_geodesic_bases_to_list()),
                    cnfg.MEANS_SURVEY.name: StaticMethod.merge_array_list(cnfg.MEANS_SURVEY.attr, self.__xml_means_surveys_to_list()),
                    cnfg.OBJECTS_REALTY.name: StaticMethod.merge_array_list(cnfg.OBJECTS_REALTY.attr, self.__xml_objects_realtys_to_list())}
        except Exception as e:
            logger.error(f"""Ошибка при формировании словаря Исходных данных {e}""")
        else:
            logger.info(f"""Словарь для исходных данных готов {_res}""")
        return _res


class XmlParcel(XMLElemenBase):

    def xml_cadnum_to_text(self):
        _ = self.node.xpath('@Definition | @CadastralNumber | @NumberRecord')
        if _:
            return _[0]
        return ''

    """
        вспомогательный класс для  обработки  общих узлов участка
        root  in [NewParcel, SubParcels, ExistParcel, ChangeParcel ... все все остальные узлы с похожей структурой]
    """
    def xml_subparcels_to_dict(self):
        """
        :return: Словарь для частей
        """
        res = dict()
        xml_node_subparcels = self.node.xpath('SubParcels')
        if xml_node_subparcels is not None and len(xml_node_subparcels) > 0:
            subparcels = XmlSubParcels(xml_node_subparcels[0])
            res = subparcels.to_dict()
            del subparcels
        return res

    def xml_ordinates_to_dict(self):
        """
        :return: Получить словарь коорлинат
        """
        res = dict()
        xml_ordinate = self.node.xpath('Contours | EntitySpatial')
        if xml_ordinate is not None and len(xml_ordinate) > 0:
            full_ord = XmlFullOrdinate(xml_ordinate[0], self.xml_cadnum_to_text())

            res = {cnfg.ENTITY_SPATIAL.name: StaticMethod.merge_array_list(cnfg.ENTITY_SPATIAL.attr,
                                                                              full_ord.full_ordinate()),
                   cnfg.BORDERS.name: StaticMethod.merge_array_list(cnfg.BORDERS.attr, full_ord.full_borders()),
                  }
            del full_ord
        return res

    def __xml_owner_to_text(self, node):
        """
            Преобразование правооблаталей
        :param node:  OwnerNeighbours
        :return:
        """
        res = ''
        try:
            for _ in node:
                rows = ''.join(_.xpath('child::NameRight/text()'))
                rows += f""" {', '.join(_.xpath('child::OwnerNeighbour/NameOwner/text()'))}"""
                rows += f""" {', '.join(_.xpath('child::OwnerNeighbour/ContactAddress/text()'))}"""
                res += f"""{ rows }; """
        finally:
            node.clear()
        return res

    def xml_related_parcel_to_list(self):
        """
        'attr': ['point', 'cadastralnumber', 'right']
        :return: list сведений о смежниках участка
        """
        _node = self.node.xpath('RelatedParcels/child::*')
        res = []
        try:
            for _ in _node:
                _rows = []
                _rows.append(''.join(_.xpath('Definition/text()')))
                _rows.append(', '.join(_.xpath('child::*/CadastralNumber/text()')))
                _rows.append(self.__xml_owner_to_text(_.xpath('child::*/OwnerNeighbours')))
                res.append(_rows)
        finally:
            _node.clear()
        return res


class XmlNewParcel(XmlParcel):
    """
        Преобразование участка на образование  в словарь
        :param root = NewParcel
    """

    def __full_addres(self, node):
        """
            Форимрование адрема
        :param node: Address
        :return: text
        """
        region = list()
        region = [StaticMethod.xml_key_to_text(node,'Region/text()', cnfg.PARCEL_COMMON.dict['address_code'])]
        region.extend(node.xpath('District/@*')[::-1])
        region.extend(node.xpath('City/@*')[::-1])
        region.extend(node.xpath('UrbanDistrict/@*')[::-1])
        region.extend(node.xpath('SovietVillage/@*')[::-1])
        region.extend(node.xpath('Locality/@*')[::-1])
        region.extend(node.xpath('Street/@*')[::-1])
        region.extend(node.xpath('Level1/@*')[::-1])
        region.extend(node.xpath('Level2/@*')[::-1])
        region.extend(node.xpath('Apartment/@*')[::-1])
        return ' '.join(region)

    def __full_utilization(self, node):
        """
            Формирование utilization
        :param node: Utilization
        :return:
        """
        try:
            res = ''
            if 'ByDoc' in node.attrib:
               res =  node.attrib['ByDoc']
            elif 'Utilization' in node.attrib:
               res = StaticMethod.xml_key_to_text(node, '@Utilization', cnfg.PARCEL_COMMON.dict['utilization'])
            elif 'LandUse' in node.attrib:
               res = StaticMethod.xml_key_to_text(node, '@LandUse',cnfg.PARCEL_COMMON.dict['landuse'])
        finally:
            node.clear()
        return res

    def full_area(self, node):
        """
            Преобразование площади

        :param node: Area
        :return: valua is the Area
        """
        result = f"""{''.join(node.xpath('Area/text()'))}±{''.join(node.xpath('Inaccuracy/text()'))}"""
        node.clear()
        return result

    def full_contours_area(self, node):
        """
        :param node: node = Contours
        :return:
        """
        _area = ' '
        # if node and len(node) > 0:
        #     _xml_area = node[0].xpath("child::*/Area")
        if node:
            for index, _ in enumerate(node,1):
                # _xml_area = _.xpath('Area')
                _area += f"""({index}) {self.full_area(_)} """
        return _area

    def __xml_general_info_to_dict(self):
        dict_address = dict()
        xml_addrss = self.node.xpath('Address')
        xml_category = self.node.xpath('Category')
        xml_utilization = self.node.xpath('Utilization | LandUse')
        if xml_addrss:
            addres=xml_addrss[0]
            dict_address['location_note'] = ''.join(addres.xpath("Other/text()"))
            type_address = addres.xpath('@AddressOrLocation')[0]
            text_address = self.__full_addres(addres)
            if type_address == '1':
                dict_address[cnfg.PARCEL_COMMON.address] = text_address
            else:
                dict_address['location'] = text_address
            xml_addrss.clear()
        if xml_category:
            dict_address['category'] = StaticMethod.xml_key_to_text(xml_category[0],'@Category',
                                                               cnfg.PARCEL_COMMON.dict['categories'])
            xml_category.clear()
        if xml_utilization:
            dict_address['utilization_landuse'] =  self.__full_utilization(xml_utilization[0])
            xml_utilization.clear()
        xml_area = self.node.xpath('Area')
        xml_area_contour = self.node.xpath('Contours/child::*/child::Area')
        if xml_area:
            dict_address['area'] = self.full_area(xml_area[0]) + '\n' + self.full_contours_area(xml_area_contour)
        dict_address['min_area'] = ''.join(self.node.xpath('MinArea/Area/text()'))
        dict_address['max_area'] = ''.join(self.node.xpath('MaxArea/Area/text()'))
        dict_address['note'] = ''.join(self.node.xpath('Note/text()'))
        dict_address['prevcadastralnumber'] = self.xml_object_realty_inner_cadastral_number_to_text()
        return dict_address

    def xml_object_realty_inner_cadastral_number_to_text(self):
        return ', '.join(self.node.xpath('ObjectRealty/InnerCadastralNumbers/child::*/text()'))


    def to_dict(self):
        res = {cnfg.PARCEL_COMMON.cadnum: self.xml_cadnum_to_text(),
               cnfg.RELATEDPARCELS.name: StaticMethod.merge_array_list(cnfg.RELATEDPARCELS.attr,
                                                                 self.xml_related_parcel_to_list()),
              }
        res.update(self.__xml_general_info_to_dict())
        res.update(self.xml_subparcels_to_dict())
        res.update(self.xml_ordinates_to_dict())
        return res


class XmlNewParcelProviding(XmlNewParcel):
    """
        Сведения о участках посредством которых обеспечивается доступ
    """

    def __get_context(self, node):
        """
        :param node: ProvidingCadastralNumber
        :return:
        """
        re = node.xpath('child::*/text()')
        re.extend(node.xpath('child::*/child::*/text()'))
        return ', '.join(re)

    def __xml_providin_to_list(self):
        _ = self.node.xpath('//ProvidingPassCadastralNumbers')
        res = []
        try:
            for i, el in enumerate(_,1):
                _def = el.getparent().xpath('@Definition')
                if not _def:
                    _def = el.getparent().xpath('@NumberRecord')
                    if not _def:
                        _def = el.getparent().xpath('@CadastralNumber')
                _definition = ''.join(_def)
                res.append([str(i), _definition, self.__get_context(el)])
        finally:
            _.clear()
        return res

    def to_dict(self):
        res = {cnfg.PROVIDING.name: StaticMethod.merge_array_list(cnfg.PROVIDING.attr,
                                                              self.__xml_providin_to_list())
               }
        return res


class XmlExistParcel(XmlNewParcel):
    """
        Фоомирования словаря значений для узлос  SpecifyRelatedParcel | ExistParcels
    """

    def __init__(self, node):
        super(XmlExistParcel,self).__init__(node)

    def xml_cadnum_to_text(self):
        number_record = ''.join(self.node.xpath('@NumberRecord'))
        str_number_record = ''
        if number_record:
            str_number_record = f"""({number_record}"""
        return f"""{ ''.join(self.node.xpath('@CadastralNumber'))} {str_number_record}"""

    def __xml_delete_all_border_to_dict(self):
        deleteAllBorder = self.node.xpath('DeleteAllBorder')
        res = dict()
        if deleteAllBorder:
            try:
                _ord = Ordinatre(self.node, CNST_EXISTPARCEL)
                res = {
                    cnfg.ENTITY_SPATIAL_EXIST.name: StaticMethod.merge_array_list(cnfg.ENTITY_SPATIAL_EXIST.attr,
                                                                                     _ord.xml_exist_ordinate_to_list()),
                    cnfg.BORDERS.name: []
                }
            finally:
                deleteAllBorder.clear()
        return res

    def __xml_all_border_to_dict(self):
        allborder = self.node.xpath('AllBorder')
        res = dict()
        if allborder and len(allborder) > 0:
            try:
                xmlfull = XmlFullOrdinate(allborder[0].xpath('Contours | EntitySpatial')[0], self.xml_cadnum_to_text())
                res = {cnfg.ENTITY_SPATIAL_EXIST.name: StaticMethod.merge_array_list(cnfg.ENTITY_SPATIAL_EXIST.attr,
                                                                                  xmlfull.full_ordinate()),
                       cnfg.BORDERS.name: StaticMethod.merge_array_list(cnfg.BORDERS.attr,
                                                                           xmlfull.full_borders()),
                       }
                del xmlfull
            finally:
                allborder.clear()
        return res

    def __xml_change_border_to_dict(self):
        changeborder = self.node.xpath('ChangeBorder')
        res = dict()
        if changeborder:
            try:
                ordinate = Ordinatre(self.node, CNST_EXISTPARCEL)
                res = {
                    cnfg.ENTITY_SPATIAL_EXIST.name: StaticMethod.merge_array_list(cnfg.ENTITY_SPATIAL_EXIST.attr,
                                                                                     ordinate.xml_exist_ordinate_to_list()),
                    cnfg.BORDERS.name: []
                }
                del ordinate
            finally:
                changeborder.clear()
        return res

    def __xml_contours_entity__to_dict(self):
        res = dict()
        xml_ordinate = self.node.xpath('Contours | EntitySpatial')
        if xml_ordinate is not None and len(xml_ordinate) > 0:
            full_ord = XmlFullOrdinate(xml_ordinate[0], self.xml_cadnum_to_text())

            res = {cnfg.ENTITY_SPATIAL_EXIST.name: StaticMethod.merge_array_list(cnfg.ENTITY_SPATIAL_EXIST.attr,
                                                                              full_ord.full_ordinate()),
                   cnfg.BORDERS.name: StaticMethod.merge_array_list(cnfg.BORDERS.attr, full_ord.full_borders()),
                   }
            del full_ord
        return res

    def __full_ordinate_to_dict(self):
        if self.node.xpath('AllBorder'):
            return self.__xml_all_border_to_dict()
        elif self.node.xpath('ChangeBorder'):
            return self.__xml_change_border_to_dict()
        elif self.node.xpath('DeleteAllBorder'):
            return self.__xml_change_border_to_dict()
        else:
            return self.__xml_contours_entity__to_dict()

    def __xml_ordinate_borders_to_dict(self):
        res = {
            cnfg.RELATEDPARCELS.name: StaticMethod.merge_array_list(cnfg.RELATEDPARCELS.attr,
                                                                self.xml_related_parcel_to_list())
        }
        res.update(self.__full_ordinate_to_dict())
        return res

    def __xml_exist___general_info(self):
        res_dict = dict()
        xml_area = self.node.xpath('Area')
        xml_area_contour = self.node.xpath('Contours/child::*/child::Area')
        if xml_area:
            res_dict[cnfg.PARCEL_COMMON.area] = self.full_area(xml_area[0]) + '\n' + self.full_contours_area(xml_area_contour)
        area_gkn = self.node.xpath('AreaInGKN/text()')
        if  area_gkn:
            res_dict[cnfg.PARCEL_COMMON.areaGKN]=  area_gkn[0]
        delta = self.node.xpath('DeltaArea/text()')
        if delta:
            res_dict[cnfg.PARCEL_COMMON.deltaArea]= delta[0]
        min_area = self.node.xpath('MinArea')
        if min_area:
            res_dict[cnfg.PARCEL_COMMON.min_area]= self.full_area(min_area[0])
        max_area = self.node.xpath('MaxArea')
        if max_area:
            res_dict[cnfg.PARCEL_COMMON.max_area]= self.full_area(max_area[0])
        res_dict[cnfg.PARCEL_COMMON.prevcadastralnumber] = self.xml_object_realty_inner_cadastral_number_to_text()
        note= self.node.xpath('Note/text()')
        if note:
            res_dict[cnfg.PARCEL_COMMON.note]= note[0]
        return  res_dict

    def to_dict(self):
        res = {cnfg.PARCEL_COMMON.cadnum: self.xml_cadnum_to_text()}
        res.update(self.__xml_exist___general_info())
        res.update(self.__xml_ordinate_borders_to_dict())
        res.update(self.xml_subparcels_to_dict())
        return res


class XmlSubParcels:
    """
        Формирования словаря значений для частей
        node: SubParcels
    """
    def __init__(self, node):
        super(XmlSubParcels, self).__init__()
        self.node = node

    def __del__(self):
        self.node.clear()

    def __xml_sub_parcels_dict(self):
        node = self.node.xpath('child::*[name()="NewSubParcel" or name()="ExistSubParcel"]')
        entity_spatial = []
        entity_spatial_ex = []
        general = []
        try:
            for index, _ in enumerate(node):
                subParcel = ElementSubParcel(_)
                if subParcel.type_ordinate == CNST_NEWPARCEL:
                     entity_spatial.append(subParcel.xml_new_dict())
                else:
                    entity_spatial_ex.append(subParcel.xml_ext_dict())
                general.append(subParcel.xml_general_dict(index+1))
                del subParcel
        finally:
            self.node.clear()
        return {cnfg.SUB_FULL_ORDINATE.name:  entity_spatial,
                cnfg.SUB_EX_FULL_ORDINATE.name: entity_spatial_ex,
                cnfg.SUBPARCEL_GENERAL.name: general}

    def to_dict(self):
        res = {cnfg.SUBPARCEL_ROWS.cadnum: ''.join(self.node.xpath('CadastralNumberParcel/text()')),
              }
        res.update(self.__xml_sub_parcels_dict())
        return res


class XmlChangeParcel(XmlNewParcel):
    """
        Формирования словаря данных для ChangeParcel(измененный участок)
    """

    def __xml_delete_entry_parcels(self):
        res = ''
        _ = self.node.xpath('DeleteEntryParcels/child::*/@*')
        if _:
            res = ', '.join(_)
            _.clear()
        return res

    def _xml_transform_entry_parcels(self):
        res = ''
        _ = self.node.xpath('TransformationEntryParcels/child::*/@*')
        if _:
            res = ', '.join(_)
            _.clear()
        return res

    def to_dict(self):
        res = {cnfg.CHANGEPARCELS.cadnum: self.xml_cadnum_to_text(),
               cnfg.CHANGEPARCELS.deleteEntyParcel: self.__xml_delete_entry_parcels(),
               cnfg.CHANGEPARCELS.transformEntryParcel: self._xml_transform_entry_parcels(),
               cnfg.CHANGEPARCELS.innerCadNum: self.xml_object_realty_inner_cadastral_number_to_text(),
               cnfg.CHANGEPARCELS.note: ''.join(self.node.xpath('Note/text()')),
              }
        res.update(self.xml_subparcels_to_dict())
        return res


class XmlConclusion(XMLElemenBase):
       """
            Чтоб не отходит от фрмата - )) - > заключение кадастрового инженера
       """

       def to_dict(self):
           return {
               cnfg.CONCLUSION['name']: self.node.text
           }
