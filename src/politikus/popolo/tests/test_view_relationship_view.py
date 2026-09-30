# -*- coding: utf-8 -*-
from politikus.popolo.testing import POLITIKUS_POPOLO_FUNCTIONAL_TESTING
from politikus.popolo.testing import POLITIKUS_POPOLO_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getMultiAdapter
from zope.interface.interfaces import ComponentLookupError

import unittest


class ViewsIntegrationTest(unittest.TestCase):

    layer = POLITIKUS_POPOLO_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        api.content.create(self.portal, 'Folder', 'other-folder')
        api.content.create(self.portal, 'Document', 'front-page')

    def test_relationship_view_is_registered(self):
        view = getMultiAdapter(
            (self.portal['other-folder'], self.portal.REQUEST),
            name='relationship-view'
        )
        self.assertTrue(view.__name__ == 'relationship-view')
        # self.assertTrue(
        #     'Sample View' in view(),
        #     'Sample View is not found in relationship-view'
        # )

    def test_relationship_view_not_matching_interface(self):
        with self.assertRaises(ComponentLookupError):
            getMultiAdapter(
                (self.portal['front-page'], self.portal.REQUEST),
                name='relationship-view'
            )


class ViewsFunctionalTest(unittest.TestCase):

    layer = POLITIKUS_POPOLO_FUNCTIONAL_TESTING

    def setUp(self):
        from plone.app.testing import TEST_USER_NAME
        from plone.app.testing import TEST_USER_PASSWORD
        from plone.testing.zope import Browser
        from zope.component import getUtility
        from zope.intid.interfaces import IIntIds
        from z3c.relationfield import RelationValue
        import datetime
        import transaction
        app = self.layer['app']
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.browser = Browser(app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization',
            'Basic {0}:{1}'.format(
                TEST_USER_NAME, TEST_USER_PASSWORD),
        )

        def relation_to(obj):
            return RelationValue(getUtility(IIntIds).getId(obj))

        self.john = api.content.create(
            self.portal, 'Person', 'john', name=u'John Doe')
        self.jane = api.content.create(
            self.portal, 'Person', 'jane', name=u'Jane Doe')
        self.relationship = api.content.create(
            self.john, 'Relationship', 'spouse',
            name=u'Spouse of Jane Doe',
            relationship_type=u'spouse',
            relationship_subject=relation_to(self.john),
            relationship_object=relation_to(self.jane),
            start_date=datetime.date(1980, 6, 1),
            end_date=datetime.date(2000, 6, 1),
        )
        transaction.commit()

    def test_relationship_view_renders(self):
        self.browser.open(self.relationship.absolute_url())
        html = self.browser.contents
        self.assertIn('Spouse of Jane Doe', html)
        self.assertIn('Spouse', html)
        self.assertIn('John Doe', html)
        self.assertIn('Jane Doe', html)
