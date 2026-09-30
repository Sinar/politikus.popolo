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
from z3c.relationfield import RelationValue

from zope.interface import alsoProvides

from politikus.popolo.content.organization import IOrganization
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

    def test_organization_view_is_registered(self):
        alsoProvides(self.portal['other-folder'], IOrganization)
        view = getMultiAdapter(
            (self.portal['other-folder'], self.portal.REQUEST),
            name='organization-view'
        )
        self.assertTrue(view.__name__ == 'organization-view')
        # self.assertTrue(
        #     'Sample View' in view(),
        #     'Sample View is not found in organization-view'
        # )

    def test_organization_view_not_matching_interface(self):
        with self.assertRaises(ComponentLookupError):
            getMultiAdapter(
                (self.portal['front-page'], self.portal.REQUEST),
                name='organization-view'
            )


class OrganizationViewMethodsTest(unittest.TestCase):
    """Test the relation-catalog query methods of OrganizationView."""

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
        self.parliament = api.content.create(
            self.portal, 'Organization', 'parliament',
            name=u'National Parliament')
        self.committee = api.content.create(
            self.portal, 'Organization', 'committee',
            name=u'Budget Committee',
            parent_organization=relation_to(self.parliament))
        self.post = api.content.create(
            self.parliament, 'Post', 'post',
            label=u'Member of Parliament',
            role=u'MP',
            organization=relation_to(self.parliament),
        )
        self.john = api.content.create(
            self.portal, 'Person', 'john', name=u'John Doe')
        self.jane = api.content.create(
            self.portal, 'Person', 'jane', name=u'Jane Doe')
        self.membership = api.content.create(
            self.parliament, 'Membership', 'membership',
            label=u'Member', role=u'MP',
            person=relation_to(self.john),
            organization=relation_to(self.parliament),
        )
        self.post_membership = api.content.create(
            self.parliament, 'Membership', 'post-membership',
            label=u'MP seat', role=u'MP',
            person=relation_to(self.jane),
            organization=relation_to(self.parliament),
            post=relation_to(self.post),
        )
        self.relationship = api.content.create(
            self.parliament, 'Relationship', 'relationship',
            name=u'Funded by',
            relationship_subject=relation_to(self.parliament),
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
            name='organization-view',
        )

    def test_child_orgs(self):
        children = self._view(self.parliament).child_orgs()
        self.assertEqual([c.id for c in children], ['committee'])
        self.assertEqual(self._view(self.committee).child_orgs(), [])

    def test_members(self):
        members = self._view(self.parliament).members()
        self.assertEqual([m.id for m in members], ['membership'])

    def test_posts(self):
        view = self._view(self.parliament)
        posts = view.posts()
        self.assertEqual([p.id for p in posts], ['post'])
        self.assertEqual(
            [m.id for m in view.post_members(posts[0])],
            ['post-membership'],
        )

    def test_relationships_subject(self):
        rels = self._view(self.parliament).relationships_subject()
        self.assertEqual([r.id for r in rels], ['relationship'])

    def test_relationships_object(self):
        self.assertEqual(self._view(self.parliament).relationships_object(),
                         [])

    def test_relationship_title(self):
        view = self._view(self.parliament)
        self.assertEqual(view.relationship_title('employer'), u'Employer')

    def test_incorporated(self):
        view = self._view(self.parliament)
        self.assertEqual(view.incorporated('KH'), u'Cambodia')

    def test_is_offshore(self):
        view = self._view(self.parliament)
        self.assertTrue(view.isOffshore('VG'))
        self.assertTrue(view.isOffshore('KY'))
        self.assertFalse(view.isOffshore('KH'))


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
        self.parliament = api.content.create(
            self.portal, 'Organization', 'parliament',
            name=u'National Parliament',
            founding_date=datetime.date(1994, 12, 12),
        )
        self.committee = api.content.create(
            self.portal, 'Organization', 'committee',
            name=u'Budget Committee',
            parent_organization=relation_to(self.parliament),
        )
        self.post = api.content.create(
            self.parliament, 'Post', 'mp-seat',
            label=u'Member of Parliament',
            role=u'MP',
            organization=relation_to(self.parliament),
        )
        self.john = api.content.create(
            self.portal, 'Person', 'john', name=u'John Doe')
        self.jane = api.content.create(
            self.portal, 'Person', 'jane', name=u'Jane Doe')
        self.membership = api.content.create(
            self.parliament, 'Membership', 'membership',
            label=u'Whip',
            role=u'Whip',
            person=relation_to(self.john),
            organization=relation_to(self.parliament),
            start_date=datetime.date(2000, 1, 1),
        )
        self.post_membership = api.content.create(
            self.parliament, 'Membership', 'post-membership',
            label=u'MP seat',
            role=u'MP',
            person=relation_to(self.jane),
            organization=relation_to(self.parliament),
            post=relation_to(self.post),
        )
        self.employer_relationship = api.content.create(
            self.parliament, 'Relationship', 'employer',
            name=u'Employer of Jane Doe',
            relationship_type=u'employer',
            relationship_subject=relation_to(self.parliament),
            relationship_object=relation_to(self.jane),
        )
        self.statement = api.content.create(
            self.parliament, 'Ownership Control Statement',
            'statement',
            title=u'Ownership statement of John Doe',
            bods_subject=relation_to(self.parliament),
            interestedParty=relation_to(self.john),
            beneficialOwnershipOrControl=True,
            interest_type=u'shareholding',
            interest_level=u'direct',
            share_exact=51.0,
        )
        transaction.commit()

    def test_organization_view_renders(self):
        self.browser.open(self.parliament.absolute_url())
        html = self.browser.contents
        self.assertIn('National Parliament', html)
        self.assertIn('Child Organization', html)
        self.assertIn('Budget Committee', html)
        self.assertIn('Posts', html)
        self.assertIn('Member of Parliament', html)
        self.assertIn('Memberships', html)
        self.assertIn('Whip', html)
        self.assertIn('John Doe', html)
        self.assertIn('Known employees', html)
        self.assertIn('Jane Doe', html)
        self.assertIn('Ownership Statements', html)
        self.assertIn('Ownership statement of John Doe', html)

    def test_organization_view_renders_child_without_parent(self):
        self.browser.open(self.committee.absolute_url())
        html = self.browser.contents
        self.assertIn('Budget Committee', html)
