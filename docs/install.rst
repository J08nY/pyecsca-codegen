============
Installation
============

This assumes that both **pyecsca** and the **pyecsca-codegen**
packages are installed as editable.

1. Checkout the ext/libtommath submodule: :code:`git submodule update --init`
2. Build the libtommath library to prepare it for the future build processes steps.

.. code-block:: shell
    cd ext
    make host stm32f0 stm32f3

Now the package should be ready with the necessary versions of
libtommath built for the host and the STM32F0 and F3 targets.
