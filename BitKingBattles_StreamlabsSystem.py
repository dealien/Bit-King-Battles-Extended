#!/usr/bin/python
# -*- coding: utf-8 -*-

""" BIT KING BATTLES EXTENDED

Bit King Battles Extended is a modified version of Bit King Battles created by VyrenGames (http://www.twitch.tv/vyrengames).
Original Bit King Battles created by Ocgineer (http://www.twitch.tv/ocgineer).

Bit King Battles is a "Bit Boss Battle" and "Stream Minions" clone made for AnkhBot
Python scripts. The main concept around these type of minigames comes down that a
current king has to be defeated by other players using cheers aka bits. When the
current king is defeated the person that dealth the killing blow will become the
new king to be defeated by others. Depending on the selected mode AND the amount of
bits used to defeat the king, the health, maximum health and shield values will
differ.

Current available modes are;
    - Shield Mode;
        Exceeding damage will be used as shield value, that has to be broken first and
        cannot be healed. Health and maximum health are taken as set, which allows for
        the new king to heal himself right after becoming the new king.

    - Overkill Mode;
        Exceeding damage will be added on top to the set base maximum health and is fully
        healed, ignoring the set base health. Initial shield can be given to new kings.

    - Strength Mode;
        The total amount of damage will become the new kings maximum health and is fully
        healed. The set maximum health will be used as minimum health value a new king
        gets.

    - Fixed Mode;
        The new king will have fixed set values for health, maximum health, and shield.
"""

# ---------------------------------------
# Import Libraries
# ---------------------------------------
import clr

clr.AddReference("IronPython.Modules.dll")

import os
import ctypes
import codecs
import re
import json

# ---------------------------------------
# Script Information
# ---------------------------------------
ScriptName = "Bit King Battles Extended"
Website = "http://www.twitch.tv/vyrengames"
Description = "Fight with points and become the new king!"
Creator = "VyrenGames"
Version = "1.0"

# ---------------------------------------
# Variables
# ---------------------------------------
# Settings file
SettingsFile = os.path.join(os.path.dirname(__file__), "BitKingBattlesSettings.json")
# Compiled regex to extract bits from IRCv3 Tags
GetBitsRegex = re.compile(r"^@.*?bits=(?P<amount>\d*);?")
# Compiled regex to extract display-name from IRCv3 Tags, unicode enabled
GetDisplayNameRegex = re.compile(r"^@.*?display-name=(?P<name>\w*);?", re.U)
# Compiled regex to verify set usernames
VerifyUsernameRegex = re.compile(r"^[a-z0-9_]{4,25}$")


# ---------------------------------------
# Classes
# ---------------------------------------
class DefaultSettings():
    """ Class Settings
        Class containing script settings with load and save functionality.
        Added to this verify own values and get/set king data to store.
        If BitKingBattlesSettings.json does not exist, it will be created using default values.
    """

    def __init__(self, settingsfile=None):
        try:
            with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8")
        except:
            self.bkb_current_name = "ankhbot"
            self.bkb_current_display = "AnkhBot"
            self.bkb_current_hp = 100
            self.bkb_current_mhp = 200
            self.bkb_current_shield = 10
            self.bkb_current_mshield = 10
            self.bkb_current_avataruri = ""
            self.bkb_new_hp = 100
            self.bkb_new_mhp = 200
            self.bkb_new_shield = 10
            self.bkb_new_mode = "Shield Mode"
            self.bkb_other_critpercent = 80
            self.bkb_chat_healnorm = "{name} healed up {healing} health with a {totalbits} health potion."
            self.bkb_chat_healcrit = "{name} critically healed up {healing} health with a {totalbits} health potion!"
            self.bkb_chat_healfull = "{name} fully healed up by using a {totalbits} health potion!"
            self.bkb_chat_healfail = "{name} tried to used a {totalbits} health potion but it had no effect."
            self.bkb_chat_killnormal = "{combatiant} mustered up {totalbits} attack power to kill the defenceless {ckname} and successfully did so by dealing {dmgtotal} health damage!"
            self.bkb_chat_killshield = "{combatiant} mustered up {totalbits} attack power to kill the shielded {ckname} and successfully did so by dealing {dmgshield} shield- and {dmghealth} health- damage!"
            self.bkb_chat_breakshieldhealthnone = "{combatiant} dealt a heavy blow of {dmgshield} damage to the shield of {name} and tore it apart!"
            self.bkb_chat_breakshieldhealthnorm = "{combatiant} skillfully broke down the shield of {name} and managed to do {dmghealth} health damage!"
            self.bkb_chat_breakshieldhealthcrit = "{combatiant} tore down the shield of {name} and dealth a massive blow of {dmghealth} health damage!"
            self.bkb_chat_shieldhitnorm = "{combatiant} dented the shield of {name} with an attack of {dmgshield}."
            self.bkb_chat_shieldhitcrit = "{combatiant} critically damaged the shield of {name} with an attack of {dmgshield}!"
            self.bkb_chat_healthhitnorm = "{combatiant} attacks and managed to scrape {dmghealth} health of {name}."
            self.bkb_chat_healthhitcrit = "{combatiant} dealt a critical blow of {dmghealth} health damage on {name}!"
            self.bkb_overlay_col_health = "rgba(65,178,0,1)"
            self.bkb_overlay_col_shield = "rgba(0,192,255,0.5)"
            self.bkb_overlay_col_damage = "rgba(153,0,3,1)"
            self.bkb_overlay_col_healing = "rgba(144,144,0,1)"
            self.bkb_overlay_col_primary = "rgba(0,0,0,0.6)"
            self.bkb_overlay_col_secondary = "rgba(0,0,0,0.5)"
            self.bkb_overlay_vol_health_norm = 0.5
            self.bkb_overlay_vol_health_crit = 0.5
            self.bkb_overlay_vol_shield_norm = 0.5
            self.bkb_overlay_vol_shield_crit = 0.5
            self.bkb_overlay_vol_heal_norm = 0.5
            self.bkb_overlay_vol_heal_crit = 0.5
            self.bkb_overlay_vol_death = 0.5
            self.use_bits = True
            self.use_points = True

    def VerifyValues(self):
        """ Verify set stored values and correct them if needed. """
        # Username verification
        if not VerifyUsernameRegex.search(self.bkb_current_name):
            ctypes.windll.user32.MessageBoxW(0,
                                             u"Warning set user name for 'Bit King Battles' is invalid.\r\n"
                                             "Use lowercase letters and underscore [a-z_] only!\r\n\r\n"
                                             "The display name allows for any capitalization or unicode names.",
                                             u"Bit King Battles Warning", 0)
        # Value verifications
        self.bkb_current_mhp = self.bkb_current_mhp if self.bkb_current_mhp > 0 else 1
        self.bkb_current_hp = self.bkb_current_hp if self.bkb_current_hp > 0 else 1
        self.bkb_current_hp = self.bkb_current_hp if self.bkb_current_hp <= self.bkb_current_mhp else self.bkb_current_mhp
        self.bkb_current_shield = self.bkb_current_shield if self.bkb_current_shield <= self.bkb_current_mshield else self.bkb_current_mshield
        self.bkb_new_mhp = self.bkb_new_mhp if self.bkb_new_mhp > 0 else 1
        self.bkb_new_hp = self.bkb_new_hp if self.bkb_new_hp > 0 else 1
        self.bkb_new_hp = self.bkb_new_hp if self.bkb_new_hp <= self.bkb_new_mhp else self.bkb_new_mhp
        self.bkb_other_critpercent = self.bkb_other_critpercent if self.bkb_other_critpercent < 100 else 100
        return

    def Reload(self, data):
        """ Reload settings from given json settings string. """
        self.__dict__ = json.loads(data, encoding="utf-8")
        return

    def Save(self, settingsfile):
        """ Save stored settings back to json and js files. """
        with codecs.open(settingsfile, encoding="utf-8-sig", mode="w+") as f:
            json.dump(self.__dict__, f, encoding="utf-8")
        with codecs.open(settingsfile.replace("json", "js"), encoding="utf-8-sig", mode="w+") as f:
            f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding='utf-8')))
        return

    def GetOverlayData(self):
        """ Returns OverlayData stored in settings """
        return OverlayData(
            self.bkb_overlay_col_health,
            self.bkb_overlay_col_shield,
            self.bkb_overlay_col_damage,
            self.bkb_overlay_col_healing,
            self.bkb_overlay_col_primary,
            self.bkb_overlay_col_secondary,
            self.bkb_overlay_vol_health_norm,
            self.bkb_overlay_vol_health_crit,
            self.bkb_overlay_vol_shield_norm,
            self.bkb_overlay_vol_shield_crit,
            self.bkb_overlay_vol_heal_norm,
            self.bkb_overlay_vol_heal_crit,
            self.bkb_overlay_vol_death
        )

    def SetKing(self, king):
        """ Update king data with a given King. """
        self.bkb_current_name = king.UserName
        self.bkb_current_display = king.DisplayName
        self.bkb_current_hp = king.Health
        self.bkb_current_mhp = king.MaxHealth
        self.bkb_current_shield = king.Shield
        self.bkb_current_mshield = king.MaxShield
        self.bkb_current_avataruri = king.AvatarUri
        return

    def GetKing(self):
        """ Returns stored king data as King. """
        return King(
            self.bkb_current_name,
            self.bkb_current_display,
            self.bkb_current_avataruri,
            self.bkb_current_hp,
            self.bkb_current_mhp,
            self.bkb_current_shield,
            self.bkb_current_mshield
        )

    def CurrencyUsed(self):
        if self.use_bits is True and self.use_points is True:
            return 2
        elif self.use_bits is True:
            return 1
        else:
            return 0


class King():
    """ Class King
        Class containing the details of a king.
    """

    def __init__(self, username, displayname, avataruri,
                 health, maxhealth, shield, maxshield):
        self.UserName = username
        self.DisplayName = displayname
        self.AvatarUri = avataruri
        self.Health = health
        self.MaxHealth = maxhealth
        self.HealthPercentage = GetPercentage(health, maxhealth)
        self.Shield = shield
        self.MaxShield = maxshield
        self.ShieldPercentage = GetPercentage(shield, maxshield)

    @classmethod
    def CopyKing(cls, king):
        """ Create a copy of given King, not a reference. """
        return cls(
            king.UserName,
            king.DisplayName,
            king.AvatarUri,
            king.Health,
            king.MaxHealth,
            king.Shield,
            king.MaxShield
        )

    def Healing(self, healAmount):
        """ This king gains health due to healing. """
        self.Health += healAmount
        self.HealthPercentage = GetPercentage(self.Health, self.MaxHealth)

    def Damage(self, healthDamage, shieldDamage):
        """ This king takes health and or shield damage. """
        self.Health -= healthDamage
        self.HealthPercentage = GetPercentage(self.Health, self.MaxHealth)
        self.Shield -= shieldDamage
        self.ShieldPercentage = GetPercentage(self.Shield, self.MaxShield)


class CombatData():
    """ Class CombatData
        Class containing various information about the combat that happened.
    """

    def __init__(self, username, displayname, isDamage, healthDamage, isHealthCrit,
                 shieldDamage, isShieldCrit, healingAmount, isHealCrit, hasShield,
                 isShieldBreak, isKill, isFullyHealed, clippedAmount, totalAmount):
        self.UserName = username
        self.DisplayName = displayname
        self.IsDamage = isDamage
        self.HealthDamage = healthDamage
        self.IsHealthCrit = isHealthCrit
        self.ShieldDamage = shieldDamage
        self.IsShieldCrit = isShieldCrit
        self.HealingAmount = healingAmount
        self.IsHealCrit = isHealCrit
        self.HasShield = hasShield
        self.IsShieldBreak = isShieldBreak
        self.IsKill = isKill
        self.IsFullyHealed = isFullyHealed
        self.ClippedAmount = clippedAmount
        self.TotalAmount = totalAmount


class OverlayData():
    """ Class OverlayData
        Class containing various overlay settings to send on refresh
    """

    def __init__(self, colHealth, colShield, colDamage, colHealing, colPrim, colSec,
                 volHealthNorm, volHealthCrit, volShieldNorm, volShieldCrit,
                 volHealNorm, volHealCrit, volDeath):
        self.ColHealth = colHealth
        self.ColShield = colShield
        self.ColDamage = colDamage
        self.ColHealing = colHealing
        self.ColPrimary = colPrim
        self.ColSecondary = colSec
        self.VolHealthNorm = volHealthNorm
        self.VolHealthCrit = volHealthCrit
        self.VolShieldNorm = volShieldNorm
        self.VolShieldCrit = volShieldCrit
        self.VolHealNorm = volHealNorm
        self.VolHealCrit = volHealCrit
        self.VolDeath = volDeath


class WsDataStruct():
    """ Class WsDataStruct
        Used to package the kings and combat data for ws transmission
    """

    def __init__(self, data, currentKing, newKing):
        self.BKBData = data
        self.CurrentKing = currentKing
        self.NewKing = newKing

    def ToJSON(self):
        """ Returns json string of containing sub classes """
        return json.dumps(self, default=lambda o: o.__dict__)


# ---------------------------------------
# Functions
# ---------------------------------------
def GetPercentage(part, whole):
    """ Function GetPercentage
        Returns percentage between part and whole rounded to
        two decimals. If whole equals zero, it returns 0.
    """
    if whole == 0:
        return 0
    else:
        return round(100.0 * part / whole, 2)


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


# ---------------------------------------
# Initialize Data on Load
# ---------------------------------------
def Init():
    # Globals
    global Settings
    global CurrentKing

    # Load in saved settings and verify values
    Settings = DefaultSettings(SettingsFile)
    Settings.VerifyValues()

    # Set King from settings
    CurrentKing = Settings.GetKing()

    # Send current king data over ws
    Parent.BroadcastWsEvent("EVENT_BKB_REFRESH", WsDataStruct(Settings.GetOverlayData(), CurrentKing, None).ToJSON())

    # End of Init
    return


# ---------------------------------------
# Reload Settings on Save
# ---------------------------------------
def ReloadSettings(data):
    # Globals
    global Settings
    global CurrentKing

    # Reload saved settings and verify values
    Settings.Reload(data)
    Settings.VerifyValues()

    # Set current king from settings
    CurrentKing = Settings.GetKing()

    # Send current king data over ws
    Parent.BroadcastWsEvent("EVENT_BKB_REFRESH", WsDataStruct(Settings.GetOverlayData(), CurrentKing, None).ToJSON())

    # End of ReloadSettings
    return


# ---------------------------------------
#    Script is enabled or disabled on UI
# ---------------------------------------
# def ScriptToggled(enabled):
#
#    # Currently this is also called when one does reload scripts
#    # and enabled will be false so we can't push refresh at this time
#    # nether can we push disabled to prevent unaccurate animations
#
#    if not enabled:
#
#        # Globals
#        global Settings
#
#        # Set current king in settings and save
#        Settings.SetKing(CurrentKing)
#        Settings.Save(SettingsFile)
#
#        # Send a disabled event over ws
#        Parent.BroadcastWsEvent("EVENT_BKB_DISABLED", None)
#
#    # End of ScriptToggled
#    return

# ---------------------------------------
#    Script is going to be unloaded
# ---------------------------------------
# def Unload():
#
#    # Globals
#    global Settings
#
#    # Set current king in settings and save
#    Settings.SetKing(CurrentKing)
#    Settings.Save(SettingsFile)
#
#    # Send a disabled event over ws
#    Parent.BroadcastWsEvent("EVENT_BKB_DISABLED", None)
#
#    # End of Unload
#    return

# ---------------------------------------
# Execute Data And Process Messages
# ---------------------------------------
def Execute(data):
    # Continue if it is a chat message
    currencyused = None
    currencyspent = 0
    if data.IsChatMessage():
        # Testing command use !bkbtest <bit-amount> and you will 'use' bits
        # If actual chat message, apply regex on raw-message to extract bits info
        if data.GetParam(0).lower() == "!bkbtest" and Parent.HasPermission(data.User, "caster", ""):
            getBitsSearch = GetBitsRegex.search("@bits=" + data.GetParam(1) + ";")
            currencyused = 'bits'
        elif data.GetParam(0).lower() == "!bkb" and RepresentsInt(data.GetParam(1)):
            getBitsSearch = GetBitsRegex.search("@bits=" + data.GetParam(1) + ";")
            currencyused = 'points'
        elif data.GetParam(0).lower() == "!bkb" and RepresentsInt(data.GetParam(1)) is False:
            Parent.SendStreamMessage('Usage: !bkb <points>')
            return False
        else:
            getBitsSearch = GetBitsRegex.search(data.RawData)
            currencyused = 'bits'
        userPoints = Parent.GetPoints(data.User)
        currencyspent = int(getBitsSearch.group("amount"))
        Parent.Log("BKB", "currencyspent = {0}".format(str(currencyspent)))
        Parent.Log("BKB", "getBitsSearch = {0}".format(str(getBitsSearch)))
        Parent.Log("BKB", "getBitsSearch.group('amount') = " + getBitsSearch.group("amount"))

    # Continue if there is a regex result and a bits/points amount is given
    if currencyspent > 0:

        # Globals
        global CurrentKing

        # Get display-name of user, if unavailable use username
        getDisplayNameSearch = GetDisplayNameRegex.search(data.RawData)
        displayName = getDisplayNameSearch.group("name") if getDisplayNameSearch.group("name") else data.User

        # if currencyused is 'points':
        #     if Parent.GetPoints(data.User) >= currencyspent:
        #         Parent.SetPoints(data.User, Parent.GetPoints(data.User) - currencyspent)
        #     else:
        #         # TODO: Add "not enough points" message to DefaultSettings()
        #         Parent.SendStreamMessage("Sorry " + displayName + ", you don't have enough points")

        # Current King uses bits -> Healing
        if data.User == CurrentKing.UserName:

            # Clip the heal amount to max health
            clippedAmount = currencyspent if CurrentKing.Health + currencyspent < CurrentKing.MaxHealth else CurrentKing.MaxHealth - CurrentKing.Health

            # It is a crit heal if heal amount is equal or bigger than the set % of missing health of current king
            isCritHeal = True if clippedAmount >= (
                    CurrentKing.MaxHealth - CurrentKing.Health) * Settings.bkb_other_critpercent / 100.0 else False

            # If is fully healed
            isFullyHealed = True if CurrentKing.Health + clippedAmount == CurrentKing.MaxHealth else False

            # Has a shield or not (not used with healing, just info to send)
            hasShield = True if CurrentKing.Shield > 0 else False

            # Set Combat data
            combatData = CombatData(
                data.User,  # Combatiant Username
                displayName,  # Combatiant Display name
                False,  # Damage (True) or Healing (False)
                0,  # Health Damage
                False,  # Health Critical Hit
                0,  # Shield Damage
                False,  # Shield Critical Hit
                clippedAmount,  # Healing Amount
                isCritHeal,  # Critical Heal
                hasShield,  # Has/Had Shield
                False,  # Shield Broke
                False,  # Current King is Killed
                isFullyHealed,  # Fully Healed up
                clippedAmount,  # Clipped total to max health
                currencyspent  # Non-clipped total
            )

            # Heal while at maximum health
            if combatData.HealingAmount == 0:

                # Chat Message Response: FAIL HEAL MESSAGE
                # If incorrect {key} is given print raw message and log it.
                try:
                    Parent.SendStreamMessage(Settings.bkb_chat_healfail.format(
                        name=combatData.DisplayName, healing=combatData.HealingAmount,
                        totalbits=combatData.TotalAmount, health=CurrentKing.Health,
                        maxhealth=CurrentKing.MaxHealth, shield=CurrentKing.Shield
                    ))
                except:
                    Parent.SendStreamMessage(Settings.bkb_chat_healfail)
                    Parent.Log("BKB", "Incorrect parameter given in 'FAIL HEAL MESSAGE'.")

            # Heal while damaged
            else:

                # Set 'new' king values with healed health
                newKing = King.CopyKing(CurrentKing)
                newKing.Healing(combatData.HealingAmount)

                # Send data to websocket > EVENT_BKB_HEAL
                Parent.BroadcastWsEvent("EVENT_BKB_HEAL", WsDataStruct(combatData, CurrentKing, newKing).ToJSON())

                # Is fully healed up
                if combatData.IsFullyHealed:

                    # Chat Message Responses: FULL HEAL MESSAGE
                    # If incorrect {key} is given print raw message and log it.
                    try:
                        Parent.SendStreamMessage(Settings.bkb_chat_healfull.format(
                            name=combatData.DisplayName, healing=combatData.HealingAmount,
                            totalbits=combatData.TotalAmount, health=CurrentKing.Health,
                            maxhealth=CurrentKing.MaxHealth, shield=CurrentKing.Shield,
                            newhealth=newKing.Health
                        ))
                    except:
                        Parent.SendStreamMessage(Settings.bkb_chat_healfull)
                        Parent.Log("BKB", "Incorrect parameter given in 'FULL HEAL MESSAGE'.")

                # It is a critical heal
                elif combatData.IsHealCrit:

                    # Chat Message Responses: CRITICAL HEAL MESSAGE
                    # If incorrect {key} is given print raw message and log it.
                    try:
                        Parent.SendStreamMessage(Settings.bkb_chat_healcrit.format(
                            name=combatData.DisplayName, healing=combatData.HealingAmount,
                            totalbits=combatData.TotalAmount, health=CurrentKing.Health,
                            maxhealth=CurrentKing.MaxHealth, shield=CurrentKing.Shield,
                            newhealth=newKing.Health
                        ))
                    except:
                        Parent.SendStreamMessage(Settings.bkb_chat_healcrit)
                        Parent.Log("BKB", "Incorrect parameter given in 'CRITICAL HEAL MESSAGE'.")

                # It is a normal heal
                else:

                    # Chat Message Responses: NORMAL HEAL MESSAGE
                    # If incorrect {key} is given print raw message and log it.
                    try:
                        Parent.SendStreamMessage(Settings.bkb_chat_healnorm.format(
                            name=combatData.DisplayName, healing=combatData.HealingAmount,
                            totalbits=combatData.TotalAmount, health=CurrentKing.Health,
                            maxhealth=CurrentKing.MaxHealth, shield=CurrentKing.Shield,
                            newhealth=newKing.Health
                        ))
                    except:
                        Parent.SendStreamMessage(Settings.bkb_chat_healnorm)
                        Parent.Log("BKB", "Incorrect parameter given in 'NORMAL HEAL MESSAGE'.")

                # Set new king data as current king
                CurrentKing = newKing

        # Another person uses bits -> Damage
        else:

            # Clip damage amount to current health + shield
            clippedAmount = currencyspent if currencyspent < CurrentKing.Health + CurrentKing.Shield else CurrentKing.Health + CurrentKing.Shield

            # Has a shield or not
            hasShield = True if CurrentKing.Shield > 0 else False

            # Calculate damage done to shield
            shieldDamage = 0 if not hasShield else (
                CurrentKing.Shield if clippedAmount >= CurrentKing.Shield else clippedAmount)

            # It is a crit shield damage if damage amount is equal or bigger than the set % of current shield durability
            isCritShield = True if hasShield and shieldDamage >= CurrentKing.Shield * Settings.bkb_other_critpercent / 100.0 else False

            # It is a shield break if the shield is destroyed
            isShieldBreak = True if hasShield and shieldDamage == CurrentKing.Shield else False

            # Calculate damage done to health
            healthDamage = 0 if CurrentKing.Shield >= clippedAmount else clippedAmount - CurrentKing.Shield

            # It is a crit health damage if damage amount (minus shield durability) is equal or bigger than the set % of current health
            isCritDamage = True if healthDamage >= CurrentKing.Health * Settings.bkb_other_critpercent / 100.0 else False

            # It is a kill if the damage is equal to the health
            isKill = True if healthDamage == CurrentKing.Health else False

            # Set Combat data
            combatData = CombatData(
                data.User,  # Combatiant username
                displayName,  # Combatiant Display name
                True,  # Damage (True) or Healing (False)
                healthDamage,  # Health Damage
                isCritDamage,  # Health Critical Hit
                shieldDamage,  # Shield Damage
                isCritShield,  # Shield Critical Hit
                0,  # Healing Amount
                False,  # Critical Heal
                hasShield,  # Has/Had Shield
                isShieldBreak,  # Shield Broke
                isKill,  # Current King is Killed
                False,  # Fully Healed up
                clippedAmount,  # Clipped total to max health
                currencyspent  # Non-clipped total
            )

            # King is killed
            if combatData.IsKill:

                # Shield Mode
                if Settings.bkb_new_mode == "Shield Mode":
                    # Calculate new shield value
                    newShield = combatData.TotalAmount - combatData.ClippedAmount
                    # Create new king
                    newKing = King(
                        combatData.UserName,
                        combatData.DisplayName,
                        "",  # AVATAR NOT IMPLEMENTED YET
                        Settings.bkb_new_hp,
                        Settings.bkb_new_mhp,
                        newShield,
                        newShield
                    )

                # Overkill Mode
                elif Settings.bkb_new_mode == "Overkill Mode":
                    # Calculate new maximum health
                    newMaxHealth = Settings.bkb_new_mhp + combatData.TotalAmount - combatData.ClippedAmount
                    # Create new king
                    newKing = King(
                        combatData.UserName,
                        combatData.DisplayName,
                        "",  # AVATAR NOT IMPLEMENTED YET
                        newMaxHealth,
                        newMaxHealth,
                        Settings.bkb_new_shield,
                        Settings.bkb_new_shield
                    )

                # Strength Mode
                elif Settings.bkb_new_mode == "Strength Mode":
                    # Calculate new maximum health
                    newMaxHealth = Settings.bkb_new_mhp if combatData.TotalAmount < Settings.bkb_new_mhp else combatData.TotalAmount
                    # Create new king
                    newKing = King(
                        combatData.UserName,
                        combatData.DisplayName,
                        "",  # AVATAR NOT IMPLEMENTED YET
                        newMaxHealth,
                        newMaxHealth,
                        Settings.bkb_new_shield,
                        Settings.bkb_new_shield
                    )

                # Fixed Mode
                else:
                    # Create new king
                    newKing = King(
                        combatData.UserName,
                        combatData.DisplayName,
                        "",  # AVATAR NOT IMPLEMENTED YET
                        Settings.bkb_new_hp,
                        Settings.bkb_new_mhp,
                        Settings.bkb_new_shield,
                        Settings.bkb_new_shield
                    )

                # Send data over to websocket > EVENT_BKB_KILL
                Parent.BroadcastWsEvent("EVENT_BKB_KILL", WsDataStruct(combatData, CurrentKing, newKing).ToJSON())

                # Killed while shielded
                if CurrentKing.Shield > 0:

                    # Chat Message Responses: KILL WHILE SHIELDED MESSAGE
                    # If incorrect {key} is given print raw message and log it.
                    try:
                        Parent.SendStreamMessage(Settings.bkb_chat_killshield.format(
                            combatiant=combatData.DisplayName, dmghealth=combatData.HealthDamage,
                            dmgshield=combatData.ShieldDamage, dmgtotal=combatData.ClippedAmount,
                            totalbits=combatData.TotalAmount, ckname=CurrentKing.DisplayName,
                            ckhealth=CurrentKing.Health, ckmaxhealth=CurrentKing.MaxHealth,
                            ckshield=CurrentKing.Shield, nkhealth=newKing.Health,
                            nkmaxhealth=newKing.MaxHealth, nkshield=newKing.Shield
                        ))
                    except:
                        Parent.SendStreamMessage(Settings.bkb_chat_killshield)
                        Parent.Log("BKB", "Incorrect parameter given in 'KILL WHILE SHIELDED MESSAGE'.")

                # Killed while defenceless
                else:

                    # Chat Message Responses: KILL WHILE UNSHIELDED MESSAGE
                    # If incorrect {key} is given print raw message and log it.
                    try:
                        Parent.SendStreamMessage(Settings.bkb_chat_killnormal.format(
                            combatiant=combatData.DisplayName, dmghealth=combatData.HealthDamage,
                            dmgshield=combatData.ShieldDamage, dmgtotal=combatData.ClippedAmount,
                            totalbits=combatData.TotalAmount, ckname=CurrentKing.DisplayName,
                            ckhealth=CurrentKing.Health, ckmaxhealth=CurrentKing.MaxHealth,
                            ckshield=CurrentKing.Shield, nkhealth=newKing.Health,
                            nkmaxhealth=newKing.MaxHealth, nkshield=newKing.Shield
                        ))
                    except:
                        Parent.SendStreamMessage(Settings.bkb_chat_killnormal)
                        Parent.Log("BKB", "Incorrect parameter given in 'KILL WHILE UNSHIELDED MESSAGE'.")

                # Set new king data as current king
                CurrentKing = newKing

            # King is not killed
            else:

                # Set 'new' king values with damaged health / shield
                newKing = King.CopyKing(CurrentKing)
                newKing.Damage(combatData.HealthDamage, combatData.ShieldDamage)

                # Send data over to websocket > EVENT_BKB_DAMAGE
                Parent.BroadcastWsEvent("EVENT_BKB_DAMAGE", WsDataStruct(combatData, CurrentKing, newKing).ToJSON())

                # King is shielded
                if combatData.HasShield:

                    # Shield breaks and takes health damage
                    # if combatData.IsShieldBreak and combatData.HealthDamage > 0:
                    if combatData.HealthDamage > 0:

                        # Shield breaks and gets a critical hit on health
                        if combatData.IsHealthCrit:

                            # Chat Message Responses: BREAK SHIELD CRITICAL HEALTH DAMAGE MESSAGE
                            # If incorrect {key} is given print raw message and log it.
                            try:
                                Parent.SendStreamMessage(Settings.bkb_chat_breakshieldhealthcrit.format(
                                    combatiant=combatData.DisplayName, dmghealth=combatData.HealthDamage,
                                    dmgshield=combatData.ShieldDamage, dmgtotal=combatData.ClippedAmount,
                                    totalbits=combatData.TotalAmount, name=CurrentKing.DisplayName,
                                    health=CurrentKing.Health, maxhealth=CurrentKing.MaxHealth,
                                    shield=CurrentKing.Shield
                                ))
                            except:
                                Parent.SendStreamMessage(Settings.bkb_chat_breakshieldhealthcrit)
                                Parent.Log("BKB",
                                           "Incorrect parameter given in 'BREAK SHIELD CRITICAL HEALTH DAMAGE MESSAGE'.")

                        # Shield breaks and gets a normal hit on health
                        else:

                            # Chat Message Responses: BREAK SHIELD NORMAL HEALTH DAMAGE MESSAGE
                            # If incorrect {key} is given print raw message and log it.
                            try:
                                Parent.SendStreamMessage(Settings.bkb_chat_breakshieldhealthnorm.format(
                                    combatiant=combatData.DisplayName, dmghealth=combatData.HealthDamage,
                                    dmgshield=combatData.ShieldDamage, dmgtotal=combatData.ClippedAmount,
                                    totalbits=combatData.TotalAmount, name=CurrentKing.DisplayName,
                                    health=CurrentKing.Health, maxhealth=CurrentKing.MaxHealth,
                                    shield=CurrentKing.Shield
                                ))
                            except:
                                Parent.SendStreamMessage(Settings.bkb_chat_breakshieldhealthnorm)
                                Parent.Log("BKB",
                                           "Incorrect parameter given in 'BREAK SHIELD NORMAL HEALTH DAMAGE MESSAGE'.")

                    # Shield breaks
                    elif combatData.IsShieldBreak:

                        # Chat Message Responses: BREAK SHIELD NO HEALTH DAMAGE MESSAGE
                        # If incorrect {key} is given print raw message and log it.
                        try:
                            Parent.SendStreamMessage(Settings.bkb_chat_breakshieldhealthnone.format(
                                combatiant=combatData.DisplayName, dmghealth=combatData.HealthDamage,
                                dmgshield=combatData.ShieldDamage, dmgtotal=combatData.ClippedAmount,
                                totalbits=combatData.TotalAmount, name=CurrentKing.DisplayName,
                                health=CurrentKing.Health, maxhealth=CurrentKing.MaxHealth,
                                shield=CurrentKing.Shield
                            ))
                        except:
                            Parent.SendStreamMessage(Settings.bkb_chat_breakshieldhealthnone)
                            Parent.Log("BKB",
                                       "Incorrect parameter given in 'BREAK SHIELD NO HEALTH DAMAGE MESSAGE'.")

                    # Shield takes damage
                    else:

                        # Critical hit on shield
                        if combatData.IsShieldCrit:

                            # Chat Message Responses: CRITICAL SHIELD DAMAGE MESSAGE
                            # If incorrect {key} is given print raw message and log it.
                            try:
                                Parent.SendStreamMessage(Settings.bkb_chat_shieldhitcrit.format(
                                    combatiant=combatData.DisplayName, dmghealth=combatData.HealthDamage,
                                    dmgshield=combatData.ShieldDamage, dmgtotal=combatData.ClippedAmount,
                                    totalbits=combatData.TotalAmount, name=CurrentKing.DisplayName,
                                    health=CurrentKing.Health, maxhealth=CurrentKing.MaxHealth,
                                    shield=CurrentKing.Shield
                                ))
                            except:
                                Parent.SendStreamMessage(Settings.bkb_chat_shieldhitcrit)
                                Parent.Log("BKB", "Incorrect parameter given in 'CRITICAL SHIELD DAMAGE MESSAGE'.")

                        # Normal hit on shield
                        else:

                            # Chat Message Responses: NORMAL SHIELD DAMAGE MESSAGE
                            # If incorrect {key} is given print raw message and log it.
                            try:
                                Parent.SendStreamMessage(Settings.bkb_chat_shieldhitnorm.format(
                                    combatiant=combatData.DisplayName, dmghealth=combatData.HealthDamage,
                                    dmgshield=combatData.ShieldDamage, dmgtotal=combatData.ClippedAmount,
                                    totalbits=combatData.TotalAmount, name=CurrentKing.DisplayName,
                                    health=CurrentKing.Health, maxhealth=CurrentKing.MaxHealth,
                                    shield=CurrentKing.Shield
                                ))
                            except:
                                Parent.SendStreamMessage(Settings.bkb_chat_shieldhitnorm)
                                Parent.Log("BKB", "Incorrect parameter given in 'NORMAL SHIELD DAMAGE MESSAGE'.")

                # King has no shield
                else:

                    # Critical hit on health
                    if combatData.IsHealthCrit:

                        # Chat Message Responses: CRITICAL HEALTH DAMAGE MESSAGE
                        # If incorrect {key} is given print raw message and log it.
                        try:
                            Parent.SendStreamMessage(Settings.bkb_chat_healthhitcrit.format(
                                combatiant=combatData.DisplayName, dmghealth=combatData.HealthDamage,
                                dmgshield=combatData.ShieldDamage, dmgtotal=combatData.ClippedAmount,
                                totalbits=combatData.TotalAmount, name=CurrentKing.DisplayName,
                                health=CurrentKing.Health, maxhealth=CurrentKing.MaxHealth,
                                shield=CurrentKing.Shield
                            ))
                        except:
                            Parent.SendStreamMessage(Settings.bkb_chat_healthhitcrit)
                            Parent.Log("BKB", "Incorrect parameter given in 'CRITICAL HEALTH DAMAGE MESSAGE'.")

                    # Normal hit on shield
                    else:

                        # Chat Message Responses: NORMAL HEALTH DAMAGE MESSAGE
                        # If incorrect {key} is given print raw message and log it.
                        try:
                            Parent.SendStreamMessage(Settings.bkb_chat_healthhitnorm.format(
                                combatiant=combatData.DisplayName, dmghealth=combatData.HealthDamage,
                                dmgshield=combatData.ShieldDamage, dmgtotal=combatData.ClippedAmount,
                                totalbits=combatData.TotalAmount, name=CurrentKing.DisplayName,
                                health=CurrentKing.Health, maxhealth=CurrentKing.MaxHealth,
                                shield=CurrentKing.Shield
                            ))
                        except:
                            Parent.SendStreamMessage(Settings.bkb_chat_healthhitcrit)
                            Parent.Log("BKB", "Incorrect parameter given in 'NORMAL HEALTH DAMAGE MESSAGE'.")

                # Set new king data as current king
                CurrentKing = newKing

        # Set current king data in settings and save
        Settings.SetKing(CurrentKing)
        Settings.Save(SettingsFile)

    return


# ---------------------------------------
# Tick
# ---------------------------------------
def Tick():
    return
