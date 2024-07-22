import os
import time
import logging

from playwright.sync_api import sync_playwright
from os.path import exists
from os.path import getsize
from systemd.journal import JournalHandler

BASE_URL = "https://www.strava.com/"

class KudosGiver:
    """
    Logins into Strava and gives kudos to all activities under
    Following.
    """
    def __init__(self, max_run_duration=540) -> None:
        self.EMAIL = os.environ.get('STRAVA_EMAIL')
        self.PASSWORD = os.environ.get('STRAVA_PASSWORD')

        if self.EMAIL is None or self.PASSWORD is None:
            raise Exception(f"Must set environ variables EMAIL AND PASSWORD. \
                e.g. run export STRAVA_EMAIL=YOUR_EMAIL")

        self.max_run_duration = max_run_duration
        self.start_time = time.time()
        self.num_entries = 100
        self.web_feed_entry_pattern = '[data-testid=web-feed-entry]'
        self.storage_file = 'session.json'

        p = sync_playwright().start()
        self.browser = p.firefox.launch() # does not work in chrome
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

        self.log = logging.getLogger('give_kudos')
        self.log.addHandler(JournalHandler())
        self.log.setLevel(logging.INFO)


    def email_login(self):
        """
        Login using email and password
        """
        self.page.goto(os.path.join(BASE_URL, 'login'))
        self.page.fill('#email', self.EMAIL)
        self.page.fill("#password", self.PASSWORD)
        self.page.click("button[type='submit']")
        self.log.info("---Logged in!!---")

    def set_session(self):
        """
        Reads the browser session from a file
        """
        self.context = self.browser.new_context(storage_state=f"{self.storage_file}")
        self.page = self.context.new_page()
        self.log.info("---Session loaded!---")

    def goto_dashboard(self):
        """
        Opens the Strava Dashboard page
        """
        self.page.goto(os.path.join(BASE_URL, f"dashboard?num_entries={self.num_entries}"))

        ## Scrolling for lazy loading elements.
        for _ in range(5):
            self.page.keyboard.press('PageDown')
            time.sleep(0.5)

        for _ in range(5):
            self.page.keyboard.press('PageUp')
            time.sleep(0.5)

        try:
            self.own_profile_id = self.page.locator(".user-menu > a").get_attribute('href').split("/athletes/")[1]
        except:
            self.log.error("can't find own profile ID")

        self.log.info("saving session data")
        self.context.storage_state(path=f"{self.storage_file}")
        self.log.info(f"own_profile_id: {self.own_profile_id}")


    def locate_kudos_buttons_and_maybe_give_kudos(self, web_feed_entry_locator) -> int:
        """
        input: playwright.locator class
        Returns count of kudos given.
        """
        w_count = web_feed_entry_locator.count()
        given_count = 0

        if w_count == 0:
            self.log.info("No data found, try relogin")
            fp = open(self.storage_file, 'w')
            fp.close()
            self.email_login()
            self.goto_dashboard()
            web_feed_entry_locator = self.page.locator(self.web_feed_entry_pattern)
            w_count = web_feed_entry_locator.count()

        self.log.info(f"web feeds found: {w_count}")
        for i in range(w_count):
            # run condition check
            curr_duration = time.time() - self.start_time
            if curr_duration > self.max_run_duration:
                self.log.warning("Max run duration reached.")
                break

            web_feed = web_feed_entry_locator.nth(i)
            p_count = web_feed.get_by_test_id("entry-header").count()

            # check if feed item is a club post
            if self.is_club_post(web_feed):
                self.log.info("club post found")
                continue

            # check if activity has multiple participants
            if p_count > 1:
                self.log.info(f"Found multiple list entries: {p_count}")
                for j in range(p_count):
                    participant = web_feed.get_by_test_id("entry-header").nth(j)
                    # ignore own activities
                    if not self.is_participant_me(participant):
                        kudos_container = web_feed.get_by_test_id("kudos_comments_container").nth(j)
                        button = self.find_unfilled_kudos_button(kudos_container)
                        given_count += self.click_kudos_button(unfilled_kudos_container=button)
            else:
                # skip if webfeed is not an activity entry
                if web_feed.get_by_test_id("owners-name").count() == 0:
                    continue
                # ignore own activities
                if not self.is_participant_me(web_feed):
                    button = self.find_unfilled_kudos_button(web_feed)
                    given_count += self.click_kudos_button(unfilled_kudos_container=button)
        self.log.info(f"Kudos given: {given_count}")
        return given_count

    def is_club_post(self, container) -> bool:
        """
        Returns true if the container is a club post
        """
        if(container.get_by_test_id("group-header").count() > 0):
            return True

        if(container.locator(".clubMemberPostHeaderLinks").count() > 0):
            return True

        return False

    def is_participant_me(self, container) -> bool:
        """
        Returns true is the container's owner is logged-in user.
        """
        owner = self.own_profile_id
        try:
            h = container.get_by_test_id("owners-name").get_attribute('href')
            hl = h.split("/athletes/")
            owner = hl[1]
        except:
            self.log.error("Some issue with getting owners-name container.")
        return owner == self.own_profile_id

    def find_unfilled_kudos_button(self, container):
        """
        Returns button as a playwright.locator class
        """
        button = None
        try:
            button = container.get_by_test_id("unfilled_kudos")
        except:
            self.log.error("Some issue with finding the unfilled_kudos container.")
        return button

    def click_kudos_button(self, unfilled_kudos_container) -> int:
        """
        input: playwright.locator class
        Returns 1 if kudos button was clicked else 0
        """
        if unfilled_kudos_container.count() == 1:
            unfilled_kudos_container.click(timeout=0, no_wait_after=True)
            self.log.info("Kudos button clicked")
            time.sleep(1)
            return 1
        return 0

    def give_kudos(self):
        """
        Interate over web feed entries
        """
        ## Give Kudos on loaded page ##
        web_feed_entry_locator = self.page.locator(self.web_feed_entry_pattern)
        self.locate_kudos_buttons_and_maybe_give_kudos(web_feed_entry_locator=web_feed_entry_locator)
        self.browser.close()


def main():
    kg = KudosGiver()
    if exists(kg.storage_file) and getsize(kg.storage_file) > 250:
        kg.set_session()
    else:
        kg.email_login()
    kg.goto_dashboard()
    kg.give_kudos()


if __name__ == "__main__":
    main()
