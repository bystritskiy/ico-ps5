# ICO PS5 native port

PS5 host changes: MIT, same licence as ico-pc. The SDL adapters retain SDL's
zlib licence notice. The Vulkan display adapter and native entry point are
adapted from the MIT PS5 host in FulGerNet/rePOP, revision
828ebf32c6abea108f4d23c174191be4faa6ae2c.

The complete executable links PS5_Vulkan and the public PS5 PayloadSDK
platform runtime (GPL-3.0-or-later); the combined native executable is subject
to those terms. The PS5_Mesa RADV archive contains components under the
licences listed in Mesa's docs/license.rst. See dependencies.json and
PS5_Vulkan's NOTICE.md for exact source revisions and runtime provenance.
The build tools, including MkPFS and DXC, retain their respective licences.

No game data, Sony SDK or PS2 BIOS is part of the port source. A local package
made with --game includes the user's own disc-derived archive. That local
package and its game data are not a source release of this port. Only the
original PAL game content from the supplied menu repack is imported; its
alternate DATA.D2 and modified executable are omitted.
