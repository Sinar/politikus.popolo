# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import politikus.popolo


class PolitikusPopoloLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import collective.vocabularies.iso
        import plone.restapi
        import politikus.bods
        self.loadZCML(package=collective.vocabularies.iso)
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=politikus.popolo)
        self.loadZCML(package=politikus.bods)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'politikus.popolo:default')
        # The site add-on installs politikus.bods on top of
        # politikus.popolo, and the popolo views depend on the
        # bods behaviors, so install it as well.
        applyProfile(portal, 'politikus.bods:default')


POLITIKUS_POPOLO_FIXTURE = PolitikusPopoloLayer()


POLITIKUS_POPOLO_INTEGRATION_TESTING = IntegrationTesting(
    bases=(POLITIKUS_POPOLO_FIXTURE,),
    name='PolitikusPopoloLayer:IntegrationTesting',
)


POLITIKUS_POPOLO_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(POLITIKUS_POPOLO_FIXTURE,),
    name='PolitikusPopoloLayer:FunctionalTesting',
)


POLITIKUS_POPOLO_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        POLITIKUS_POPOLO_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='PolitikusPopoloLayer:AcceptanceTesting',
)
