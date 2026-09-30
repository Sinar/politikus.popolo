# -*- coding: utf-8 -*-
"""View tests for the content types that use the default Dexterity view."""
from politikus.popolo.testing import POLITIKUS_POPOLO_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing import setRoles
from plone.testing.zope import Browser

import datetime
import transaction
import unittest


class DefaultViewsFunctionalTest(unittest.TestCase):

    layer = POLITIKUS_POPOLO_FUNCTIONAL_TESTING

    def setUp(self):
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

    def _render(self, obj):
        self.browser.open(obj.absolute_url())
        return self.browser.contents

    def test_area_view_renders(self):
        area = api.content.create(
            self.portal, 'Area', 'area',
            name=u'Kericho',
            classification=u'P.PPL',
        )
        transaction.commit()
        html = self._render(area)
        self.assertIn('Kericho', html)

    def test_contact_detail_view_renders(self):
        person = api.content.create(
            self.portal, 'Person', 'person', name=u'John Doe')
        detail = api.content.create(
            person, 'Contact Detail', 'phone',
            label=u'Mobile',
            value=u'+254 700 000 000',
        )
        detail.type = u'cell'
        transaction.commit()
        html = self._render(detail)
        self.assertIn('Mobile', html)
        self.assertIn('+254 700 000 000', html)

    def test_identifier_view_renders(self):
        person = api.content.create(
            self.portal, 'Person', 'person', name=u'John Doe')
        identifier = api.content.create(
            person, 'Identifier', 'tin',
            scheme=u'TIN',
            identifier=u'1234567',
        )
        transaction.commit()
        html = self._render(identifier)
        self.assertIn('TIN', html)
        self.assertIn('1234567', html)

    def test_other_name_view_renders(self):
        person = api.content.create(
            self.portal, 'Person', 'person', name=u'John Doe')
        other = api.content.create(
            person, 'Other Name', 'nickname',
            name=u'Johnny',
            start_date=datetime.date(1990, 1, 1),
            end_date=datetime.date(2000, 1, 1),
        )
        transaction.commit()
        html = self._render(other)
        self.assertIn('Johnny', html)
