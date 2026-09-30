# -*- coding: utf-8 -*-
from politikus.popolo.testing import POLITIKUS_POPOLO_FUNCTIONAL_TESTING
from politikus.popolo.testing import POLITIKUS_POPOLO_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface.interfaces import ComponentLookupError
from zope.intid.interfaces import IIntIds

from zope.interface import alsoProvides

from politikus.popolo.content.membership import IMembership
from z3c.relationfield import RelationValue

import transaction
import unittest


def relation_to(obj):
    """A storable RelationValue pointing at the given content object."""
    return RelationValue(getUtility(IIntIds).getId(obj))


class ViewsIntegrationTest(unittest.TestCase):

    layer = POLITIKUS_POPOLO_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        api.content.create(self.portal, 'Folder', 'other-folder')
        api.content.create(self.portal, 'Document', 'front-page')

    def test_membership_view_is_registered(self):
        alsoProvides(self.portal['other-folder'], IMembership)
        view = getMultiAdapter(
            (self.portal['other-folder'], self.portal.REQUEST),
            name='membership-view'
        )
        self.assertTrue(view.__name__ == 'membership-view')
        # self.assertTrue(
        #     'Sample View' in view(),
        #     'Sample View is not found in membership-view'
        # )

    def test_membership_view_not_matching_interface(self):
        with self.assertRaises(ComponentLookupError):
            getMultiAdapter(
                (self.portal['front-page'], self.portal.REQUEST),
                name='membership-view'
            )


class ViewsFunctionalTest(unittest.TestCase):

    layer = POLITIKUS_POPOLO_FUNCTIONAL_TESTING

    def setUp(self):
        from plone.app.testing import TEST_USER_NAME
        from plone.app.testing import TEST_USER_PASSWORD
        from plone.testing.zope import Browser
        import datetime
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

        self.john = api.content.create(
            self.portal, 'Person', 'john', name=u'John Doe')
        self.parliament = api.content.create(
            self.portal, 'Organization', 'parliament',
            name=u'National Parliament')
        self.committee = api.content.create(
            self.portal, 'Organization', 'committee',
            name=u'Budget Committee')
        self.post = api.content.create(
            self.parliament, 'Post', 'mp-seat',
            label=u'Member of Parliament',
            role=u'MP',
            organization=relation_to(self.parliament),
        )
        self.membership = api.content.create(
            self.parliament, 'Membership', 'membership',
            label=u'MP for Kericho',
            role=u'MP',
            person=relation_to(self.john),
            organization=relation_to(self.parliament),
            post=relation_to(self.post),
            on_behalf_of=relation_to(self.committee),
            start_date=datetime.date(2000, 1, 1),
            end_date=datetime.date(2010, 1, 1),
        )
        transaction.commit()

    def test_membership_view_renders(self):
        self.browser.open(self.membership.absolute_url())
        html = self.browser.contents
        self.assertIn('MP for Kericho', html)
        self.assertIn('John Doe', html)
        self.assertIn('National Parliament', html)
        self.assertIn('Member of Parliament', html)
        self.assertIn('On Behalf Of', html)
        self.assertIn('Budget Committee', html)

    def test_membership_view_renders_without_relations(self):
        bare = api.content.create(
            self.parliament, 'Membership', 'bare',
            label=u'Bare membership',
            role=u'Advisor',
            person=relation_to(self.john),
            organization=relation_to(self.parliament),
        )
        transaction.commit()
        self.browser.open(bare.absolute_url())
        self.assertIn('Bare membership', self.browser.contents)
