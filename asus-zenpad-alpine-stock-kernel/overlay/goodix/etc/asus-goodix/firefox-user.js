// SPDX-License-Identifier: GPL-3.0-only
// Appliance profile preferences; Firefox sandbox defaults are unchanged.
user_pref("browser.uidensity", 2);
user_pref("layout.css.devPixelsPerPx", "1.25");
user_pref("browser.cache.disk.enable", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("startup.homepage_welcome_url", "");
user_pref("startup.homepage_welcome_url.additional", "");
user_pref("browser.startup.firstrunSkipsHomepage", true);
user_pref("browser.startup.page", 0);

// Keep an unclean media session from restarting without an explicit play.
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("media.autoplay.default", 5);

// Reduce decorative browser/page animation on the software framebuffer.
// Keep APZ/native touch, process isolation, and decoder sandboxes unchanged.
user_pref("ui.prefersReducedMotion", 1);
