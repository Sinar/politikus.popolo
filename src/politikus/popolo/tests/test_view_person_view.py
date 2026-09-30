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

from politikus.popolo.content.person import IPerson
from z3c.relationfield import RelationValue

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

    def test_person_view_is_registered(self):
        alsoProvides(self.portal['other-folder'], IPerson)
        view = getMultiAdapter(
            (self.portal['other-folder'], self.portal.REQUEST),
            name='person-view'
        )
        self.assertTrue(view.__name__ == 'person-view')
        # self.assertTrue(
        #     'Sample View' in view(),
        #     'Sample View is not found in person-view'
        # )

    def test_person_view_not_matching_interface(self):
        with self.assertRaises(ComponentLookupError):
            getMultiAdapter(
                (self.portal['front-page'], self.portal.REQUEST),
                name='person-view'
            )


class PersonViewMethodsTest(unittest.TestCase):
    """Test the relation-catalog query methods of PersonView."""

    layer = POLITIKUS_POPOLO_INTEGRATION_TESTING

    def setUp(self):
        from plone.app.testing import TEST_USER_NAME
        from plone.app.testing import login
        from zope.security.management import newInteraction
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        # The view methods use zope.security.checkPermission, which needs
        # a security manager and a zope.security interaction.
        login(self.portal, TEST_USER_NAME)
        newInteraction()
        self.john = api.content.create(
            self.portal, 'Person', 'john', name=u'John Doe')
        self.jane = api.content.create(
            self.portal, 'Person', 'jane', name=u'Jane Doe')
        self.organization = api.content.create(
            self.portal, 'Organization', 'organization',
            name=u'Acme Corporation')
        self.membership = api.content.create(
            self.organization, 'Membership', 'membership',
            label=u'Member', role=u'Member',
            person=relation_to(self.john),
            organization=relation_to(self.organization),
        )
        self.relationship = api.content.create(
            self.john, 'Relationship', 'relationship',
            name=u'Spouse of',
            relationship_subject=relation_to(self.john),
            relationship_object=relation_to(self.jane),
        )

    def tearDown(self):
        from plone.app.testing import logout
        from zope.security.management import endInteraction
        endInteraction()
        logout()

    def _view(self, content):
        return getMultiAdapter(
            (content, self.portal.REQUEST),
            name='person-view',
        )

    def test_memberships(self):
        memberships = self._view(self.john).memberships()
        self.assertEqual([m.id for m in memberships], ['membership'])
        self.assertEqual(self._view(self.jane).memberships(), [])

    def test_relationships_subject(self):
        rels = self._view(self.john).relationships_subject()
        self.assertEqual([r.id for r in rels], ['relationship'])

    def test_relationships_object(self):
        rels = self._view(self.jane).relationships_object()
        self.assertEqual([r.id for r in rels], ['relationship'])
        self.assertEqual(self._view(self.john).relationships_object(), [])

    def test_relationship_title(self):
        view = self._view(self.john)
        self.assertEqual(view.relationship_title('spouse'), u'Spouse')

    def test_nationalities(self):
        view = self._view(self.john)
        self.assertEqual(view.nationalities('KH'), u'Cambodia')


class ViewsFunctionalTest(unittest.TestCase):

    layer = POLITIKUS_POPOLO_FUNCTIONAL_TESTING

    def setUp(self):
        from plone.app.testing import TEST_USER_NAME
        from plone.app.testing import TEST_USER_PASSWORD
        from plone.testing.zope import Browser
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
        self.john = api.content.create(
            self.portal, 'Person', 'john',
            name=u'John Doe',
            gender=u'male',
            birth_date=datetime.date(1950, 5, 4),
            death_date=datetime.date(2020, 5, 4),
        )
        self.jane = api.content.create(
            self.portal, 'Person', 'jane',
            name=u'Jane Doe')
        self.organization = api.content.create(
            self.portal, 'Organization', 'acme',
            name=u'Acme Corporation')
        self.post = api.content.create(
            self.organization, 'Post', 'chairman',
            label=u'Chairman',
            role=u'Chairman',
            organization=relation_to(self.organization),
        )
        self.membership = api.content.create(
            self.organization, 'Membership', 'chairman-membership',
            label=u'Chairman of Acme',
            role=u'Chairman',
            person=relation_to(self.john),
            organization=relation_to(self.organization),
            post=relation_to(self.post),
            start_date=datetime.date(2000, 1, 1),
        )
        self.relationship = api.content.create(
            self.john, 'Relationship', 'spouse',
            name=u'Spouse of Jane Doe',
            relationship_type=u'spouse',
            relationship_subject=relation_to(self.john),
            relationship_object=relation_to(self.jane),
        )
        transaction.commit()

    def test_person_fti_registers_nationalities_behavior(self):
        """The politikus.bods nationalities behavior must be enabled
        on the Person type, or the nationalities data of the
        person view is unavailable."""
        from zope.component import queryUtility
        from plone.dexterity.interfaces import IDexterityFTI
        fti = queryUtility(IDexterityFTI, name='Person')
        self.assertIn(
            'politikus.bods.nationalities',
            fti.behaviors,
        )

    def test_person_view_renders(self):
        self.browser.open(self.john.absolute_url())
        html = self.browser.contents
        self.assertIn('John Doe', html)
        self.assertIn('Membership and Posts', html)
        self.assertIn('Chairman of Acme', html)
        self.assertIn('Acme Corporation', html)
        self.assertIn('Family Relationships', html)
        self.assertIn('Jane Doe', html)

    def test_person_view_renders_nationalities(self):
        import transaction
        self.john.nationalities = ['KH']
        transaction.commit()
        self.browser.open(self.john.absolute_url())
        html = self.browser.contents
        self.assertIn('Nationalities', html)
        self.assertIn('Cambodia', html)
