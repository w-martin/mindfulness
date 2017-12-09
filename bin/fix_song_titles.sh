#!/bin/sh
BASE_DIR=$(crudini --get mindfulness_config.ini general path)
$BASE_DIR/bin/mindfulness --fix-titles-and-exit
