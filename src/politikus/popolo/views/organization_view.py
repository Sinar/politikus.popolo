# -*- coding: utf-8 -*-

from plone import api
from politikus.popolo import _
from Products.Five.browser import BrowserView
from plone.dexterity.browser.view import DefaultView
import politikus.popolo.utils as utils

from Acquisition import aq_inner
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.security import checkPermission
from zc.relation.interfaces import ICatalog
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import IVocabularyFactory


class OrganizationView(DefaultView, BrowserView):
    # If you want to define a template here, please remove the template from
    # the configure.zcml registration of this view.
    # template = ViewPageTemplateFile('organization_view.pt')

    # TODO These are old functions, and could be rewritten better.

    def child_orgs(self):
        """
        Return back references from source object on specified attribute_name
        """
        catalog = getUtility(ICatalog)
        intids = getUtility(IIntIds)

        source_object = self.context
        attribute_name = 'parent_organization'

        result = []

        for rel in catalog.findRelations(
            dict(to_id=intids.getId(aq_inner(source_object)),
                 from_attribute=attribute_name)
              ):

            obj = intids.queryObject(rel.from_id)

            if obj is not None and checkPermission('zope2.View', obj):
                result.append(obj)

        return result

    def members(self):
        """
        Return back references from source object on specified attribute_name
        """
        catalog = getUtility(ICatalog)
        intids = getUtility(IIntIds)

        source_object = self.context
        attribute_name = 'organization'

        result = []

        for rel in catalog.findRelations(
            dict(to_id=intids.getId(aq_inner(source_object)),
                 from_attribute=attribute_name)
              ):

            obj = intids.queryObject(rel.from_id)

            if obj is not None and checkPermission('zope2.View', obj):
                if obj.portal_type == 'Membership' and obj.post is None:
                    # check if person has membership
                    if obj.person:
                        result.append(obj)

        return result

    def posts(self):
        """
        Return back references from source object on specified attribute_name
        """
        catalog = getUtility(ICatalog)
        intids = getUtility(IIntIds)

        source_object = self.context
        attribute_name = 'organization'

        result = []

        for rel in catalog.findRelations(
            dict(to_id=intids.getId(aq_inner(source_object)),
                 from_attribute=attribute_name)
              ):

            obj = intids.queryObject(rel.from_id)

            if obj is not None and checkPermission('zope2.View', obj):
                if obj.portal_type == 'Post':

                    result.append(obj)

        return result

    def post_members(self, post):
        """
        Return the memberships known to hold the given post, without
        writing them onto the post object while the view renders.
        """
        catalog = getUtility(ICatalog)
        intids = getUtility(IIntIds)

        members = []

        for rel in catalog.findRelations(
            dict(to_id=intids.getId(aq_inner(post)),)
              ):
            member = intids.queryObject(rel.from_id)
            if member is None:
                continue
            # check for person
            if member.person:
                members.append(member)

        return members

    def relationships_subject(self):
        # Get relationships where person or organization is the subject

        """
        Return back references from source object on specified attribute_name
        """
        catalog = getUtility(ICatalog)
        intids = getUtility(IIntIds)

        source_object = self.context

        result = []

        for rel in catalog.findRelations(
            dict(to_id=intids.getId(aq_inner(source_object)),
                 from_attribute='relationship_subject')
              ):

            obj = intids.queryObject(rel.from_id)

            if obj is not None and checkPermission('zope2.View', obj):
                result.append(obj)

        return result

    def relationships_object(self):
        # Get relationships where person or organization is the object

        """
        Return back references from source object on specified attribute_name
        """
        catalog = getUtility(ICatalog)
        intids = getUtility(IIntIds)

        source_object = self.context

        result = []

        for rel in catalog.findRelations(
            dict(to_id=intids.getId(aq_inner(source_object)),
                 from_attribute='relationship_object')
              ):

            obj = intids.queryObject(rel.from_id)

            if obj is not None and checkPermission('zope2.View', obj):
                result.append(obj)

        return result

    def relationship_title(self, value):

        factory = getUtility(IVocabularyFactory,
                             'politikus.popolo.relationshiptypes')

        vocabulary = factory(self)

        term = vocabulary.getTerm(value)

        return term.title

    def incorporated(self, value):
        factory = getUtility(
                IVocabularyFactory,
                'collective.vocabularies.iso.countries')

        vocabulary = factory(self)
        term = vocabulary.getTerm(value)

        return term.title

    def isOffshore(self, value):

        factory = getUtility(
                        IVocabularyFactory,
                        'collective.vocabularies.iso.countries')

        vocabulary = factory(self)
        term = vocabulary.getTerm(value)
        
        # Declare common offshore havens  
        offshore = ['VG', 'KY', 'PA', 'BS']

        if any(term.value in country for country in offshore):
            return True
        else:
            return False
