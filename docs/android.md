# BRouter Motorcycle Profiles – Android Installation

## 1. Purpose

This document describes how to install and use the motorcycle routing profiles
with BRouter and OsmAnd on Android.

The procedure has been validated with:

    BRouter 1.7.10 (57)
    OsmAnd 5.3.10

The current release contains three user-facing profiles:

    moto-fast
    moto-curvy
    moto-very-curvy


## 2. Prerequisites

The following applications must already be installed and configured:

- BRouter
- OsmAnd

BRouter routing segments for the region in which routing will be performed must
also be installed.

Before installing the motorcycle profiles, verify that normal BRouter routing
works on the device.


## 3. Release Profiles

The profiles intended for normal use are located in the repository under:

    release/

The current files are:

    release/moto-fast.brf
    release/moto-curvy.brf
    release/moto-very-curvy.brf

Only these files are required on the Android device.

The additional profiles under:

    profiles/

are development and calibration profiles and are not required for normal use.


## 4. Transfer Profiles to Android

Transfer the `.brf` files from the computer to the Android device.

For normal use, **LocalSend is the recommended simple method**:

1. send the three files from `release/`,
2. receive them on Android,
3. move them with the Android file manager into BRouter's existing `profiles2`
   directory.

Other transfer methods such as USB, network file transfer or cloud storage are
also valid.

For development and diagnostics, ADB can be used. On the validated Carpe Iter
v4c setup the direct command is:

```bash
adb push release/moto-fast.brf          release/moto-curvy.brf          release/moto-very-curvy.brf   /storage/emulated/0/Android/media/btools.routingapp/brouter/profiles2/
```

When using LocalSend, transferred files normally arrive in the Android
Downloads area first.


## 5. Locate the BRouter profiles2 Directory

BRouter stores custom routing profiles in its `profiles2` directory.

On the validated Carpe Iter v4c setup, the physical path is:

```text
/storage/emulated/0/Android/media/btools.routingapp/brouter/profiles2
```

On other Android devices or BRouter versions the path may differ, so the
existing BRouter directory should always be preferred over creating a new one.

On recent Android versions, the system Files application can make this
slightly confusing.

The entries shown at the top level such as:

    Images
    Videos
    Audio
    Documents
    Downloads

are Android content categories and do not necessarily correspond directly to
ordinary directories at the same filesystem level.

The actual device storage is normally shown separately using the device name.

The BRouter `profiles2` directory may also appear under the Android
"Documents" category because `.brf` files are recognised as documents.

Do not create a new `profiles2` directory merely because the physical path is
not immediately visible.

Instead, locate the existing BRouter `profiles2` directory.


## 6. Determine the Physical profiles2 Location

A reliable way to find the actual BRouter profile directory is:

1. Open the Android Files application.
2. Open `Documents`.
3. Locate `profiles2`.
4. Open an existing `.brf` file or display its file information.
5. Determine the physical storage location from the file details.

The exact path may depend on the Android version and BRouter storage
configuration.

Use the existing directory that BRouter itself created.


## 7. Copy the Profiles

Copy the three release files into the existing BRouter `profiles2` directory:

    moto-fast.brf
    moto-curvy.brf
    moto-very-curvy.brf

If the files were transferred using LocalSend, this normally means moving them
from:

    Downloads

into the BRouter `profiles2` directory.

Do not rename the `.brf` files.

The filename is important because OsmAnd uses it to select the BRouter profile.


## 8. Verify the Profile in BRouter

Before configuring OsmAnd, verify that BRouter can see the installed profile.

Start BRouter.

From the BRouter main screen, open:

    BRouter App

The installed profile should be available in the profile selection.

For example:

    moto-fast

Select it.

If BRouter accepts the profile, the installation location and profile syntax
are valid.

BRouter may then display controls such as:

    Server Mode
    Profile Settings
    Select from

and wait for waypoint selection.

It is not necessary to calculate a route manually in BRouter for the OsmAnd
integration test.

The important result is that BRouter recognises the custom profile.


## 9. OsmAnd Integration

OsmAnd can use BRouter as an external offline routing engine.

For each motorcycle routing character, create a corresponding OsmAnd profile.

The OsmAnd profile name is significant.

Use the following names exactly:

    Brouter[moto-fast]

    Brouter[moto-curvy]

    Brouter[moto-very-curvy]

The value inside the square brackets corresponds to the BRouter profile
filename without the `.brf` extension.

For example:

    OsmAnd profile:

        Brouter[moto-fast]

    BRouter profile:

        moto-fast.brf


## 10. Configure the OsmAnd Routing Engine

For each of the three OsmAnd profiles, configure BRouter as the routing engine.

In the navigation settings for the profile, select the external offline
routing engine:

    BRouter (offline)

The exact menu wording may vary slightly between OsmAnd versions.

The important configuration is:

    OsmAnd profile
        |
        v
    BRouter offline routing
        |
        v
    profile name in [...]
        |
        v
    corresponding .brf file


## 11. Fast Profile

Create or duplicate an OsmAnd motorcycle profile and name it:

    Brouter[moto-fast]

Configure:

    Routing engine:
        BRouter (offline)

This profile prioritises efficient motorcycle travel.

Motorways remain available and may be selected when they provide a meaningful
travel-time advantage.


## 12. Curvy Profile

Create or duplicate another OsmAnd motorcycle profile and name it:

    Brouter[moto-curvy]

Configure:

    Routing engine:
        BRouter (offline)

This profile accepts moderate additional travel cost in order to prefer more
attractive motorcycle roads.


## 13. Very Curvy Profile

Create or duplicate another OsmAnd motorcycle profile and name it:

    Brouter[moto-very-curvy]

Configure:

    Routing engine:
        BRouter (offline)

This profile applies a stronger motorcycle-road preference and may accept
larger reasonable deviations from the fastest route.


## 14. Recommended OsmAnd Setup

A convenient OsmAnd setup therefore contains three motorcycle profiles:

    Brouter[moto-fast]
    Brouter[moto-curvy]
    Brouter[moto-very-curvy]

This allows the rider to switch routing behaviour directly from OsmAnd without
changing files or BRouter configuration.


## 15. End-to-End Validation

The installation has been validated using the complete chain:

    generated .brf profile
            |
            v
    Android BRouter
            |
            v
    OsmAnd
            |
            v
    BRouter offline routing
            |
            v
    calculated route

All three release profiles have been successfully loaded and used for route
calculation on Android.


## 16. Behaviour Validation

The Android routes were compared with routes generated by the local BRouter
development and calibration environment.

The three profiles produced the expected routing behaviour:

    Fast
        efficient route

    Curvy
        motorcycle-oriented alternative

    Very Curvy
        stronger motorcycle-oriented alternative

This confirms that the generated release profiles behave consistently between
the local BRouter development environment and the Android target environment.


## 17. Recommended Test Route

A useful route for verifying profile differentiation is:

    Bern -> Luzern

This route provides meaningful alternatives between efficient major-road
routing and more motorcycle-oriented secondary-road corridors.

It has therefore also been used during development calibration.

Depending on current BRouter routing data and OpenStreetMap data, exact route
geometry may change over time.


## 18. Troubleshooting: Profile Does Not Appear in BRouter

If a profile does not appear in BRouter:

1. verify that the file is in BRouter's existing `profiles2` directory,
2. verify that the filename ends in `.brf`,
3. verify that the file was copied rather than merely selected in the Android
   Documents category,
4. restart BRouter.

If necessary, inspect an existing working `.brf` file in the Android Files
application and compare its physical location with the custom profile.


## 19. Troubleshooting: OsmAnd Cannot Calculate a Route

If OsmAnd cannot calculate a route:

1. verify that BRouter can see the profile,
2. verify that the OsmAnd profile name contains the correct BRouter profile
   name,
3. verify that BRouter offline routing is selected,
4. verify that the required BRouter routing segments are installed.

For example:

    Brouter[moto-curvy]

must correspond to:

    moto-curvy.brf

A spelling difference can cause routing to fail.


## 20. Troubleshooting: BRouter Is Not Available in OsmAnd

If BRouter is not available as an external offline routing engine:

1. verify that BRouter is installed,
2. start BRouter at least once,
3. verify that BRouter itself is functional,
4. completely restart OsmAnd,
5. check the routing-engine selection again.


## 21. Updating Profiles

When a newer version of the motorcycle profiles is released, replace the
existing `.brf` files in BRouter's `profiles2` directory.

As long as the filenames remain unchanged:

    moto-fast.brf
    moto-curvy.brf
    moto-very-curvy.brf

the existing OsmAnd profile configuration can continue to be used.

There is no need to recreate the OsmAnd profiles for every routing-profile
update.


## 22. Development vs User Installation

Normal Android users do not need:

- Python
- the profile generator
- the BRouter standalone server
- calibration tools
- development presets

They only need:

    BRouter
    OsmAnd
    BRouter routing data
    release/*.brf

The generated release profiles are deliberately committed to the repository so
that they can be installed directly.


## 23. Current Compatibility Status

The current installation procedure has been successfully tested with:

    BRouter:
        1.7.10 (57)

    OsmAnd:
        5.3.10
        2026-05-06 release

    Profiles:
        moto-fast.brf
        moto-curvy.brf
        moto-very-curvy.brf

Other recent versions may also work, but should not be described as validated
until tested.


## 24. Future Segment-Based Routing

The current Android integration applies one BRouter profile to an OsmAnd
routing profile.

The longer-term project vision allows routing intentions to be selected per
route segment.

For example:

    Biel -> Bern
        Fast

    Bern -> Thun
        Curvy

    Thun -> Brienz
        Very Curvy

    Brienz -> Andermatt
        Curvy

This future planning functionality is outside the scope of the initial Android
release.

The current three profiles provide the routing foundation for that future
model.

## 22. v1 Deployment Validation

The v1 release deployment was validated end-to-end on a Carpe Iter v4c.

The three release files were installed in:

```text
/storage/emulated/0/Android/media/btools.routingapp/brouter/profiles2
```

BRouter recognised all three profiles:

```text
moto-fast
moto-curvy
moto-very-curvy
```

OsmAnd successfully exposed the installed profile using the expected external
router naming, for example:

```text
BRouter[moto-curvy]
Type router (offline)
```

This validates the v1 deployment chain:

```text
release/*.brf
    ->
Android profiles2
    ->
BRouter
    ->
OsmAnd
    ->
offline routing
```

For ordinary installation, LocalSend plus the Android file manager is simpler
than ADB. ADB remains useful for development, diagnostics and exact path
verification.
