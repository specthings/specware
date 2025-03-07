# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the validation module. """

# Copyright (C) 2020, 2024 embedded brains GmbH & Co. KG
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import pytest

from specitems import EmptyItemCache, Item, ItemCache, item_is_enabled

from specware import (augment_with_test_case_links, generate_validation,
                      SpecWareTypeProvider, TransitionMap)

from .util import create_item_cache


def test_validation(tmpdir):
    base_directory = os.path.join(tmpdir, "base")
    validation_config = {
        "base-directory-map": [{
            "source": "/does/not/exist",
            "target": "?"
        }, {
            "source":
            os.path.normpath(
                os.path.join(os.path.dirname(__file__), "spec-validation")),
            "target":
            base_directory
        }]
    }

    generate_validation(validation_config, EmptyItemCache())

    item_cache = create_item_cache(tmpdir, "spec-validation")
    augment_with_test_case_links(item_cache)

    transition_map = TransitionMap(item_cache["/directive"])
    assert transition_map.pre_co_idx_to_co_name(0) == "Name"
    assert transition_map.post_co_idx_st_idx_to_st_name(0, 0) == "Ok"
    assert transition_map.post_co_idx_to_co_name(0) == "Status"
    assert len(list(transition_map.get_variants([]))) == 36
    assert len(list(transition_map.get_variants(["RTEMS_MULTIPROCESSING"
                                                 ]))) == 36
    assert len(list(transition_map.get_post_conditions([]))) == 4
    assert len(
        list(transition_map.get_post_conditions(["RTEMS_MULTIPROCESSING"
                                                 ]))) == 5
    transition_map = TransitionMap(item_cache["/action2"])
    assert transition_map.skip_idx_to_name(2) == "SkipReason"
    assert len(list(transition_map.get_post_conditions(["BOOM"]))) == 6
    transition_map = TransitionMap(item_cache["/action3"])
    assert len(list(transition_map.get_post_conditions(["RTEMS_SMP"]))) == 9

    generate_validation(validation_config, item_cache)
    generate_validation(validation_config, item_cache, ["fet.c", "ts.c"])

    with open(os.path.join(base_directory, "fet.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup Fet
 */

/*
 * Copyright (C) 2024 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <fet.h>
#include <rtems.h>
#include <rtems/bspIo.h>
#include <rtems/sysinit.h>
#include <rtems/test-info.h>
#include <rtems/testopts.h>
#include <rtems/score/atomic.h>

#include "fet-local.h"
#include "tx-support.h"

#include <rtems/test.h>

/**
 * @defgroup Fet spec:/fet
 *
 * @ingroup RTEMSTestSuites
 *
 * @brief The FET brief description.
 *
 * The FET description.
 *
 * @{
 */

static void FatalErrorTestCase(
  rtems_fatal_source source,
  rtems_fatal_code   code
)
{
  /* FET - Fet */
}

/* FET support */

static rtems_fatal_source fatal_error_test_source;

static rtems_fatal_code fatal_error_test_code;

T_TEST_CASE(Fet)
{
  FatalErrorTestCase( fatal_error_test_source, fatal_error_test_code );
}

const char rtems_test_name[] = "Fet";

static char fatal_error_test_buffer[ 512 ];

static const T_action fatal_error_test_actions[] = {
  T_report_hash_sha256
};

static const T_config fatal_error_test_config = {
  .name = rtems_test_name,
  .buf = fatal_error_test_buffer,
  .buf_size = sizeof( fatal_error_test_buffer ),
  .putchar = rtems_put_char,
  .verbosity = RTEMS_TEST_VERBOSITY,
#if defined(CONFIGURE_APPLICATION_NEEDS_CLOCK_DRIVER)
  .now = T_now_clock,
#else
  .now = T_now_tick,
#endif
  .allocate = T_memory_allocate,
  .deallocate = T_memory_deallocate,
  .action_count = T_ARRAY_SIZE( fatal_error_test_actions ),
  .actions = fatal_error_test_actions
};

static bool fatal_error_test_initialized;

static void FatalErrorTestInitialize( void )
{
  if ( !fatal_error_test_initialized ) {
    fatal_error_test_initialized = true;
    rtems_test_begin( rtems_test_name, TEST_STATE );
    T_register();
    T_run_initialize( &fatal_error_test_config );
  }
}

static Atomic_Uint fatal_error_test_counter;

static void FatalErrorTestExtension(
  rtems_fatal_source source,
  bool always_set_to_false,
  rtems_fatal_code code
)
{
  rtems_fatal_code exit_code;

  (void) always_set_to_false;

  if ( source == RTEMS_FATAL_SOURCE_EXIT ) {
    return;
  }

  if (
    _Atomic_Fetch_add_uint(
      &fatal_error_test_counter,
      1,
      ATOMIC_ORDER_RELAXED
    ) != 0
  ) {
    return;
  }

  fatal_error_test_source = source;
  fatal_error_test_code = code;
  FatalErrorTestInitialize();
  T_make_runner();
  T_run_all();

  if ( T_run_finalize() ) {
    rtems_test_end( rtems_test_name );
    exit_code = 0;
  } else {
    exit_code = 1;
  }

  rtems_fatal( RTEMS_FATAL_SOURCE_EXIT, exit_code );
}

RTEMS_SYSINIT_ITEM(
  FatalErrorTestInitialize,
  RTEMS_SYSINIT_BSP_EARLY,
  RTEMS_SYSINIT_ORDER_FIRST
);

#if !defined(CONFIGURE_MAXIMUM_FILE_DESCRIPTORS)
#define CONFIGURE_MAXIMUM_FILE_DESCRIPTORS 0

#define CONFIGURE_APPLICATION_DISABLE_FILESYSTEM
#endif

#define CONFIGURE_DISABLE_NEWLIB_REENTRANCY

#ifdef FATAL_ERROR_TEST_INITIAL_EXTENSION
#define OPTIONAL_FATAL_ERROR_TEST_INITIAL_EXTENSION \\
  FATAL_ERROR_TEST_INITIAL_EXTENSION,
#else
#define OPTIONAL_FATAL_ERROR_TEST_INITIAL_EXTENSION
#endif

#define CONFIGURE_INITIAL_EXTENSIONS \\
  OPTIONAL_FATAL_ERROR_TEST_INITIAL_EXTENSION \\
  { .fatal = FatalInitialExtension }, \\
  { .fatal = FatalErrorTestExtension }

#if !defined(CONFIGURE_RTEMS_INIT_TASKS_TABLE)

#define CONFIGURE_IDLE_TASK_INITIALIZES_APPLICATION

#if !defined(CONFIGURE_IDLE_TASK_BODY)

#define CONFIGURE_IDLE_TASK_BODY IdleBody

void *IdleBody( uintptr_t ignored )
{
  (void) ignored;

  rtems_fatal( RTEMS_FATAL_SOURCE_EXIT, 1 );
}

#endif /* CONFIGURE_IDLE_TASK_BODY */

#endif /* CONFIGURE_IDLE_TASK_INITIALIZES_APPLICATION */

#define CONFIGURE_INIT

#include <rtems/confdefs.h>

/** @} */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "ts.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup Ts
 */

/*
 * Copyright (C) 2020 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <blue.h>

#include "green.h"

#include <rtems/test.h>

/**
 * @defgroup Ts spec:/ts
 *
 * @ingroup RTEMSTestSuites
 *
 * @brief The Blue Green brief description.
 *
 * The Blue Green description.
 *
 * @{
 */

/* Blue green code for Ts */

/** @} */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "tc12.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup Directive
 * @ingroup Tc
 * @ingroup Tc2
 */

/*
 * Copyright (C) 2020 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <a.h>
#include <b.h>
#include <rtems.h>

#include "x.h"
#include "y.h"

#include <rtems/test.h>

/**
 * @defgroup Directive spec:/directive
 *
 * @ingroup Ts
 *
 * @brief Test rtems_task_ident() brief description.
 *
 * Test rtems_task_ident() description.
 *
 * @{
 */

typedef enum {
  Directive_Pre_Name_Invalid,
  Directive_Pre_Name_Self,
  Directive_Pre_Name_Valid,
  Directive_Pre_Name_NA
} Directive_Pre_Name;

typedef enum {
  Directive_Pre_Node_Local,
  Directive_Pre_Node_Remote,
  Directive_Pre_Node_Invalid,
  Directive_Pre_Node_SearchAll,
  Directive_Pre_Node_SearchOther,
  Directive_Pre_Node_SearchLocal,
  Directive_Pre_Node_NA
} Directive_Pre_Node;

typedef enum {
  Directive_Pre_Id_NullPtr,
  Directive_Pre_Id_Valid,
  Directive_Pre_Id_NA
} Directive_Pre_Id;

typedef enum {
  Directive_Post_Status_Ok,
  Directive_Post_Status_InvAddr,
  Directive_Post_Status_InvName,
  Directive_Post_Status_InvNode,
  Directive_Post_Status_InvId,
  Directive_Post_Status_NA
} Directive_Post_Status;

typedef enum {
  Directive_Post_Id_Nop,
  Directive_Post_Id_NullPtr,
  Directive_Post_Id_Self,
  Directive_Post_Id_LocalTask,
  Directive_Post_Id_RemoteTask,
  Directive_Post_Id_NA
} Directive_Post_Id;

typedef struct {
  uint16_t Skip : 1;
  uint16_t Pre_Name_NA : 1;
  uint16_t Pre_Node_NA : 1;
  uint16_t Pre_Id_NA : 1;
  uint16_t Post_Status : 3;
  uint16_t Post_Id : 3;
} Directive_Entry;

/**
 * @brief Test context for spec:/directive test case.
 */
typedef struct {
  /**
   * @brief Brief context member description.
   *
   * Context member description.
   */
  rtems_status_code status;

  rtems_name name;

  uint32_t node;

  rtems_id *id;

  rtems_id id_value;

  rtems_id id_local_task;

  rtems_id id_remote_task;

  struct {
    /**
     * @brief This member defines the pre-condition states for the next action.
     */
    size_t pcs[ 3 ];

    /**
     * @brief If this member is true, then the test action loop is executed.
     */
    bool in_action_loop;

    /**
     * @brief This member contains the next transition map index.
     */
    size_t index;

    /**
     * @brief This member contains the current transition map entry.
     */
    Directive_Entry entry;

    /**
     * @brief If this member is true, then the current transition variant
     *   should be skipped.
     */
    bool skip;
  } Map;
} Directive_Context;

static Directive_Context
  Directive_Instance;

static const char * const Directive_PreDesc_Name[] = {
  "Invalid",
  "Self",
  "Valid",
  "NA"
};

static const char * const Directive_PreDesc_Node[] = {
  "Local",
  "Remote",
  "Invalid",
  "SearchAll",
  "SearchOther",
  "SearchLocal",
  "NA"
};

static const char * const Directive_PreDesc_Id[] = {
  "NullPtr",
  "Valid",
  "NA"
};

static const char * const * const Directive_PreDesc[] = {
  Directive_PreDesc_Name,
  Directive_PreDesc_Node,
  Directive_PreDesc_Id,
  NULL
};

/* Test rtems_task_ident() support */

static void Directive_Pre_Name_Prepare(
  Directive_Context *ctx,
  Directive_Pre_Name state
)
{
  /* Prologue */

  switch ( state ) {
    case Directive_Pre_Name_Invalid: {
      /*
       * The name parameter shall not equal to a name of an active Classic API
       * task object and not equal to RTEMS_SELF.
       */
      ctx->name = 1;
      break;
    }

    case Directive_Pre_Name_Self: {
      /*
       * The name parameter shall be RTEMS_SELF.
       */
      ctx->name = RTEMS_SELF;
      break;
    }

    case Directive_Pre_Name_Valid: {
      /*
       * The name parameter shall equal to a name of an active Classic API task
       * object.
       */
      ctx->name = rtems_build_name( 'T', 'A', 'S', 'K' );
      break;
    }

    case Directive_Pre_Name_NA:
      break;
  }

  /* Epilogue */
}

static void Directive_Pre_Node_Prepare(
  Directive_Context *ctx,
  Directive_Pre_Node state
)
{
  switch ( state ) {
    case Directive_Pre_Node_Local: {
      /*
       * The node parameter shall be the local node number.
       */
      ctx->node = 1;
      break;
    }

    case Directive_Pre_Node_Remote: {
      /*
       * The node parameter shall be a remote node number.
       */
      ctx->node = 2;
      break;
    }

    case Directive_Pre_Node_Invalid: {
      /*
       * The node parameter shall be an invalid node number.
       */
      ctx->node = 256;
      break;
    }

    case Directive_Pre_Node_SearchAll: {
      /*
       * The node parameter shall be RTEMS_SEARCH_ALL_NODES.
       */
      ctx->node = RTEMS_SEARCH_ALL_NODES;
      break;
    }

    case Directive_Pre_Node_SearchOther: {
      /*
       * The node parameter shall be RTEMS_SEARCH_OTHER_NODES.
       */
      ctx->node = RTEMS_SEARCH_OTHER_NODES;
      break;
    }

    case Directive_Pre_Node_SearchLocal: {
      /*
       * The node parameter shall be RTEMS_SEARCH_LOCAL_NODE.
       */
      ctx->node = RTEMS_SEARCH_LOCAL_NODE;
      break;
    }

    case Directive_Pre_Node_NA:
      break;
  }
}

static void Directive_Pre_Id_Prepare(
  Directive_Context *ctx,
  Directive_Pre_Id   state
)
{
  switch ( state ) {
    case Directive_Pre_Id_NullPtr: {
      /*
       * The id parameter shall be NULL.
       */
      ctx->id = NULL;
      break;
    }

    case Directive_Pre_Id_Valid: {
      /*
       * The id parameter shall point to an object identifier.
       */
      ctx->id_value = 0xffffffff;
      ctx->id = &ctx->id_value;
      break;
    }

    case Directive_Pre_Id_NA:
      break;
  }
}

static void Directive_Post_Status_Check(
  Directive_Context    *ctx,
  Directive_Post_Status state
)
{
  switch ( state ) {
    case Directive_Post_Status_Ok: {
      /*
       * The status shall be RTEMS_SUCCESSFUL.
       */
      T_rsc(ctx->status, RTEMS_SUCCESSFUL);
      break;
    }

    case Directive_Post_Status_InvAddr: {
      /*
       * The status shall be RTEMS_INVALID_ADDRESS.
       */
      T_rsc(ctx->status, RTEMS_INVALID_ADDRESS);
      break;
    }

    case Directive_Post_Status_InvName: {
      /*
       * The status shall be RTEMS_INVALID_NAME.
       */
      T_rsc(ctx->status, RTEMS_INVALID_NAME);
      break;
    }

    case Directive_Post_Status_InvNode: {
      /*
       * The status shall be RTEMS_INVALID_NODE.
       */
      T_rsc(ctx->status, RTEMS_INVALID_NODE);
      break;
    }

    case Directive_Post_Status_InvId: {
      /*
       * The status shall be RTEMS_INVALID_ID.
       */
      T_rsc(ctx->status, RTEMS_INVALID_ID);
      break;
    }

    case Directive_Post_Status_NA:
      break;
  }
}

static void Directive_Post_Id_Check(
  Directive_Context *ctx,
  Directive_Post_Id  state
)
{
  switch ( state ) {
    case Directive_Post_Id_Nop: {
      /*
       * The value of the object identifier referenced by the id parameter
       * shall be the value before the call to rtems_task_ident().
       */
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, 0xffffffff);
      break;
    }

    case Directive_Post_Id_NullPtr: {
      /*
       * The id parameter shall be NULL.
       */
      T_null(ctx->id)
      break;
    }

    case Directive_Post_Id_Self: {
      /*
       * The value of the object identifier referenced by the id parameter
       * shall be the identifier of the executing thread.
       */
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, rtems_task_self());
      break;
    }

    case Directive_Post_Id_LocalTask: {
      /*
       * The value of the object identifier referenced by the id parameter
       * shall be the identifier of a local task with a name equal to the name
       * parameter.  If more than one local task with such a name exists, then
       * it shall be the identifier of the task with the lowest object index.
       */
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, ctx->id_local_task);
      break;
    }

    case Directive_Post_Id_RemoteTask: {
      /*
       * The value of the object identifier referenced by the id parameter
       * shall be the identifier of a remote task on a eligible node defined by
       * the node parameter with a name equal to the name parameter.  If more
       * than one task with such a name exists on the same node, then it shall
       * be the identifier of the task with the lowest object index.  If more
       * than one task with such a name exists on different eligible nodes,
       * then it shall be the identifier of the task with the lowest node
       * index.
       */
      T_eq_ptr(ctx->id, &ctx->id_value);
      T_eq_u32(ctx->id_value, ctx->id_remote_task);
      break;
    }

    case Directive_Post_Id_NA:
      break;
  }
}

/**
 * @brief Setup brief description.
 *
 * Setup description.
 */
static void Directive_Setup( Directive_Context *ctx )
{
  rtems_status_code sc;

  sc = rtems_task_create(
    rtems_build_name( 'T', 'A', 'S', 'K' ),
    1,
    RTEMS_MINIMUM_STACK_SIZE,
    RTEMS_DEFAULT_MODES,
    RTEMS_DEFAULT_ATTRIBUTES,
    &ctx->id_local_task
  );
  T_assert_rsc_success( sc );
}

static void Directive_Setup_Wrap( void *arg )
{
  Directive_Context *ctx;

  ctx = arg;
  ctx->Map.in_action_loop = false;
  Directive_Setup( ctx );
}

static void Directive_Teardown( Directive_Context *ctx )
{
  rtems_status_code sc;

  if ( ctx->id_local_task != 0 ) {
    sc = rtems_task_delete( ctx->id_local_task );
    T_rsc_success( sc );
  }
}

static void Directive_Teardown_Wrap( void *arg )
{
  Directive_Context *ctx;

  ctx = arg;
  ctx->Map.in_action_loop = false;
  Directive_Teardown( ctx );
}

static void Directive_Action( Directive_Context *ctx )
{
  ctx->status = rtems_task_ident( ctx->name, ctx->node, ctx->id );
}

static const Directive_Entry
Directive_Entries[] = {
  { 0, 0, 0, 0, Directive_Post_Status_InvAddr, Directive_Post_Id_NullPtr },
  { 0, 0, 0, 0, Directive_Post_Status_InvName, Directive_Post_Id_Nop },
  { 0, 0, 0, 0, Directive_Post_Status_Ok, Directive_Post_Id_Self },
  { 0, 0, 0, 0, Directive_Post_Status_Ok, Directive_Post_Id_LocalTask },
#if defined(RTEMS_MULTIPROCESSING)
  { 0, 0, 0, 0, Directive_Post_Status_Ok, Directive_Post_Id_RemoteTask }
#else
  { 0, 0, 0, 0, Directive_Post_Status_InvName, Directive_Post_Id_Nop }
#endif
};

static const uint8_t
Directive_Map[] = {
  0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 2, 0, 2, 0, 2, 0, 2, 0, 3,
  0, 4, 0, 1, 0, 3, 0, 4, 0, 3
};

static size_t Directive_Scope( void *arg, char *buf, size_t n )
{
  Directive_Context *ctx;

  ctx = arg;

  if ( ctx->Map.in_action_loop ) {
    return T_get_scope( Directive_PreDesc, buf, n, ctx->Map.pcs );
  }

  return 0;
}

static T_fixture Directive_Fixture = {
  .setup = Directive_Setup_Wrap,
  .stop = NULL,
  .teardown = Directive_Teardown_Wrap,
  .scope = Directive_Scope,
  .initial_context = &Directive_Instance
};

static inline Directive_Entry Directive_PopEntry( Directive_Context *ctx )
{
  size_t index;

  index = ctx->Map.index;
  ctx->Map.index = index + 1;
  return Directive_Entries[
    Directive_Map[ index ]
  ];
}

static void Directive_TestVariant( Directive_Context *ctx )
{
  Directive_Pre_Name_Prepare( ctx, ctx->Map.pcs[ 0 ] );
  Directive_Pre_Node_Prepare( ctx, ctx->Map.pcs[ 1 ] );
  Directive_Pre_Id_Prepare( ctx, ctx->Map.pcs[ 2 ] );
  Directive_Action( ctx );
  Directive_Post_Status_Check( ctx, ctx->Map.entry.Post_Status );
  Directive_Post_Id_Check( ctx, ctx->Map.entry.Post_Id );
}

/**
 * @fn void T_case_body_Directive( void )
 */
T_TEST_CASE_FIXTURE( Directive, &Directive_Fixture )
{
  Directive_Context *ctx;

  ctx = T_fixture_context();
  ctx->Map.in_action_loop = true;
  ctx->Map.index = 0;

  for (
    ctx->Map.pcs[ 0 ] = Directive_Pre_Name_Invalid;
    ctx->Map.pcs[ 0 ] < Directive_Pre_Name_NA;
    ++ctx->Map.pcs[ 0 ]
  ) {
    for (
      ctx->Map.pcs[ 1 ] = Directive_Pre_Node_Local;
      ctx->Map.pcs[ 1 ] < Directive_Pre_Node_NA;
      ++ctx->Map.pcs[ 1 ]
    ) {
      for (
        ctx->Map.pcs[ 2 ] = Directive_Pre_Id_NullPtr;
        ctx->Map.pcs[ 2 ] < Directive_Pre_Id_NA;
        ++ctx->Map.pcs[ 2 ]
      ) {
        ctx->Map.entry = Directive_PopEntry( ctx );
        Directive_TestVariant( ctx );
      }
    }
  }
}

/** @} */

/**
 * @defgroup Tc spec:/tc
 *
 * @ingroup Ts
 *
 * @brief Test case brief description.
 *
 * Test case description. Is contained in spec:/ts.
 *
 * This test case performs the following actions:
 *
 * - Test case action 0 description.
 *
 *   - Test case action 0 check 0 description.
 *
 *   - Test case action 0 check 1 description.
 *
 * - Test case action 1 description.
 *
 *   - Test case action 1 check 0 description.
 *
 *   - Test case action 1 check 1 description.
 *
 * @{
 */

/* Test case support code */

/**
 * @brief Test case action 0 description.
 */
static void Tc_Action_0( void )
{
  /* Test case action 0 code */

  /*
   * Test case action 0 check 0 description.
   */
  /* Test case action 0 check 0 code: Accounts for 123 test plan steps */

  /*
   * Test case action 0 check 1 description.
   */
  /* Test case action 0 check 1 code; step 123 */
}

/**
 * @brief Test case action 1 description.
 */
static void Tc_Action_1( void )
{
  /* Test case action 1 code */

  /*
   * Test case action 1 check 0 description.
   */
  /* Test case action 1 check 0 code; step 124 */

  /*
   * Test case action 1 check 1 description.
   */
  /* Test case action 1 check 1 code */
}

/**
 * @fn void T_case_body_Tc( void )
 */
T_TEST_CASE( Tc )
{
  T_plan( 125 );

  Tc_Action_0();
  Tc_Action_1();
}

/** @} */

/**
 * @defgroup Tc2 spec:/tc2
 *
 * @ingroup Ts
 *
 * @brief Test case 2 brief description.
 *
 * Test case 2 description.
 *
 * This test case performs the following actions:
 *
 * - Test case 2 action 0 description.
 *
 *   - Test case 2 action 0 check 0 description.
 *
 *   - Test case 2 action 0 check 1 description.
 *
 * - Test case 2 action 1 description.
 *
 * - Test case 2 action 2 description.
 *
 *   - Test case 2 action 2 check 0 description.
 *
 * @{
 */

/**
 * @brief Test context for spec:/tc2 test case.
 */
typedef struct {
  /**
   * @brief Context member brief.
   *
   * Context member description.
   */
  int member;
} Tc2_Context;

static Tc2_Context
  Tc2_Instance;

/**
 * @brief Setup brief.
 *
 * Setup description.
 */
static void Tc2_Setup( void )
{
  /* Setup code */
}

static void Tc2_Setup_Wrap( void *arg )
{
  (void) arg;
  Tc2_Setup();
}

static T_fixture Tc2_Fixture = {
  .setup = Tc2_Setup_Wrap,
  .stop = NULL,
  .teardown = NULL,
  .scope = NULL,
  .initial_context = &Tc2_Instance
};

/**
 * @brief Test case 2 action 0 description.
 */
static void Tc2_Action_0( void )
{
  /* Test case 2 action 0 code */

  /*
   * Test case 2 action 0 check 0 description.
   */
  /* Test case 2 action 0 check 0 code */

  /*
   * Test case 2 action 0 check 1 description.
   */
  /* Test case 2 action 0 check 1 code */
}

/**
 * @brief Test case 2 action 1 description.
 */
static void Tc2_Action_1( Tc2_Context *ctx )
{
  /* Test case 2 action 1 code with ctx */
}

/**
 * @brief Test case 2 action 2 description.
 */
static void Tc2_Action_2( Tc2_Context *ctx )
{
  /* Test case 2 action 2 code */

  /*
   * Test case 2 action 2 check 0 description.
   */
  /* Test case 2 action 2 check 0 code with ctx */
}

/**
 * @fn void T_case_body_Tc2( void )
 */
T_TEST_CASE_FIXTURE( Tc2, &Tc2_Fixture )
{
  Tc2_Context *ctx;

  ctx = T_fixture_context();

  Tc2_Action_0();
  Tc2_Action_1( ctx );
  Tc2_Action_2( ctx );
}

/** @} */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "tc34.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup Rtm
 * @ingroup Tc10
 * @ingroup Tc3
 * @ingroup Tc4
 * @ingroup Tc5
 * @ingroup Tc6
 * @ingroup Tc7
 * @ingroup Tc8
 * @ingroup Tc9
 */

/*
 * Copyright (C) 2020, 2025 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <c.h>
#include <u.h>

#include "v.h"
#include "z.h"

#include <rtems/test.h>

/**
 * @defgroup Rtm spec:/rtm
 *
 * @ingroup Ts
 *
 * @brief Test brief.
 *
 * Test description.
 *
 * @{
 */

/* Context support code */

/**
 * @brief Test context for spec:/rtm test case.
 */
typedef struct {
  /**
   * @brief Context member brief.
   *
   * Context member description.
   */
  int member;

  /**
   * @brief This member references the measure runtime context.
   */
  T_measure_runtime_context *context;

  /**
   * @brief This member provides the measure runtime request.
   */
  T_measure_runtime_request request;

  /**
   * @brief This member provides an optional measurement begin time point.
   */
  T_ticks begin;

  /**
   * @brief This member provides an optional measurement end time point.
   */
  T_ticks end;
} Rtm_Context;

static Rtm_Context
  Rtm_Instance;

/* Support code */

static void Rtm_Setup_Context( Rtm_Context *ctx )
{
  T_measure_runtime_config config;

  memset( &config, 0, sizeof( config ) );
  config.sample_count = 100;
  ctx->request.arg = ctx;
  ctx->request.flags = T_MEASURE_RUNTIME_REPORT_SAMPLES;
  ctx->context = T_measure_runtime_create( &config );
  T_assert_not_null( ctx->context );
}

static void Rtm_Setup_Wrap( void *arg )
{
  Rtm_Context *ctx;

  ctx = arg;
  Rtm_Setup_Context( ctx );
}

/**
 * @brief Stop brief.
 *
 * Stop description.
 */
static void Rtm_Stop( void )
{
  /* Stop code */
}

static void Rtm_Stop_Wrap( void *arg )
{
  (void) arg;
  Rtm_Stop();
}

/**
 * @brief Teardown brief.
 *
 * Teardown description.
 */
static void Rtm_Teardown( void )
{
  /* Teardown code */
}

static void Rtm_Teardown_Wrap( void *arg )
{
  (void) arg;
  Rtm_Teardown();
}

static T_fixture Rtm_Fixture = {
  .setup = Rtm_Setup_Wrap,
  .stop = Rtm_Stop_Wrap,
  .teardown = Rtm_Teardown_Wrap,
  .scope = NULL,
  .initial_context = &Rtm_Instance
};

/**
 * @brief Cleanup brief.
 *
 * Cleanup description.
 */
static void Rtm_Cleanup( void )
{
  /* Cleanup code */
}

/**
 * @defgroup Rpr spec:/rpr
 *
 * @{
 */

/**
 * @brief Body brief.
 *
 * Body description.
 */
static void Rpr_Body( void )
{
  /* Body code */
}

static void Rpr_Body_Wrap( void *arg )
{
  (void) arg;
  Rpr_Body();
}

/**
 * @brief Teardown brief.
 *
 * Teardown description.
 */
static bool Rpr_Teardown( void )
{
  /* Teardown code */
}

static bool Rpr_Teardown_Wrap(
  void        *arg,
  T_ticks     *delta,
  uint32_t     tic,
  uint32_t     toc,
  unsigned int retry
)
{
  (void) arg;
  (void) delta;
  (void) tic;
  (void) toc;
  (void) retry;
  return Rpr_Teardown();
}

/**
 * @brief Cleanup brief.
 *
 * Cleanup description.
 */
static void Rpr_Cleanup( void )
{
  /* Cleanup code */
}

/** @} */

#if defined(FOOBAR)
/**
 * @defgroup Rpr2 spec:/rpr2
 *
 * @{
 */

/**
 * @brief Body brief.
 *
 * Body description.
 */
static void Rpr2_Body( void )
{
  /* Body code */
}

static void Rpr2_Body_Wrap( void *arg )
{
  (void) arg;
  Rpr2_Body();
}

/** @} */
#endif

/**
 * @fn void T_case_body_Rtm( void )
 */
T_TEST_CASE_FIXTURE( Rtm, &Rtm_Fixture )
{
  Rtm_Context *ctx;

  ctx = T_fixture_context();

  ctx->request.name = "Rpr";
  ctx->request.setup = NULL;
  ctx->request.body = Rpr_Body_Wrap;
  ctx->request.teardown = Rpr_Teardown_Wrap;
  T_measure_runtime( ctx->context, &ctx->request );
  Rpr_Cleanup();
  Rtm_Cleanup();

  #if defined(FOOBAR)
  ctx->request.name = "Rpr2";
  ctx->request.setup = NULL;
  ctx->request.body = Rpr2_Body_Wrap;
  ctx->request.teardown = NULL;
  T_measure_runtime( ctx->context, &ctx->request );
  Rtm_Cleanup();
  #endif
}

/** @} */

/**
 * @defgroup Tc10 spec:/tc10
 *
 * @ingroup Ts
 *
 * @brief Test case 10 brief description.
 *
 * Test case 10 description.
 *
 * This test case performs the following actions:
 *
 * - Test case 10 action 0 description.
 *
 * @{
 */

/**
 * @brief Test context for spec:/tc10 test case.
 */
typedef struct {
  /**
   * @brief Context 10 member brief.
   *
   * Context 10 member description.
   */
  int member;
} Tc10_Context;

static Tc10_Context
  Tc10_Instance;

static T_fixture Tc10_Fixture = {
  .setup = NULL,
  .stop = NULL,
  .teardown = NULL,
  .scope = NULL,
  .initial_context = &Tc10_Instance
};

/**
 * @brief Test case 10 action 0 description.
 */
static void Tc10_Action_0( Tc10_Context *ctx )
{
  /* Test case 10 action 0 code with ctx */
}

void Tc10_Run( void )
{
  Tc10_Context *ctx;

  ctx = T_case_begin( "Tc10", &Tc10_Fixture );

  Tc10_Action_0( ctx );

  T_case_end();
}

/** @} */

/**
 * @defgroup Tc3 spec:/tc3
 *
 * @ingroup Ts
 *
 * @brief Test case 3 brief description.
 *
 * Test case 3 description.
 *
 * This test case performs the following actions:
 *
 * - Test case 3 action 0 description.
 *
 *   - Test case 3 action 0 check 0 description.
 *
 * @{
 */

/**
 * @brief Test case 3 action 0 description.
 */
static void Tc3_Action_0( void )
{
  /* Test case 3 action 0 code */

  /*
   * Test case 3 action 0 check 0 description.
   */
  /* Test case 3 action 0 check 0 code; step 0 */
}

/**
 * @fn void T_case_body_Tc3( void )
 */
T_TEST_CASE( Tc3 )
{
  T_plan( 1 );

  Tc3_Action_0();
}

/** @} */

/**
 * @defgroup Tc4 spec:/tc4
 *
 * @ingroup Ts
 *
 * @brief Test case 4 brief description.
 *
 * Test case 4 description.
 *
 * @{
 */

/**
 * @fn void T_case_body_Tc4( void )
 */
T_TEST_CASE( Tc4 )
{
}

/** @} */

/**
 * @defgroup Tc5 spec:/tc5
 *
 * @ingroup Ts
 *
 * @brief Test case 5 brief description.
 *
 * Test case 5 description.
 *
 * This test case performs the following actions:
 *
 * - Test case action 0 description.
 *
 *   - Test case action 0 check 0 description.
 *
 *   - Test case action 0 check 1 description.
 *
 * - Test case action 1 description.
 *
 *   - Test case action 1 check 0 description.
 *
 *   - Test case action 1 check 1 description.
 *
 * @{
 */

/**
 * @brief Test context for spec:/tc5 test case.
 */
typedef struct {
  /**
   * @brief This member contains a copy of the corresponding Tc5_Run()
   *   parameter.
   */
  int *a;

  /**
   * @brief This member contains a copy of the corresponding Tc5_Run()
   *   parameter.
   */
  int b;

  /**
   * @brief This member contains a copy of the corresponding Tc5_Run()
   *   parameter.
   */
  int *c;
} Tc5_Context;

static Tc5_Context
  Tc5_Instance;

static T_fixture Tc5_Fixture = {
  .setup = NULL,
  .stop = NULL,
  .teardown = NULL,
  .scope = NULL,
  .initial_context = &Tc5_Instance
};

/**
 * @brief Test case action 0 description.
 */
static void Tc5_Action_0( void )
{
  /* Test case action 0 code */

  /*
   * Test case action 0 check 0 description.
   */
  /* Test case action 0 check 0 code */

  /*
   * Test case action 0 check 1 description.
   */
  /* Test case action 0 check 1 code; step 0 */
}

/**
 * @brief Test case action 1 description.
 */
static void Tc5_Action_1( void )
{
  /* Test case action 1 code */

  /*
   * Test case action 1 check 0 description.
   */
  /* Test case action 1 check 0 code; step 1 */

  /*
   * Test case action 1 check 1 description.
   */
  /* Test case action 1 check 1 code */
}

void Tc5_Run( int *a, int b, int *c )
{
  Tc5_Context *ctx;

  ctx = &Tc5_Instance;
  ctx->a = a;
  ctx->b = b;
  ctx->c = c;

  ctx = T_case_begin( "Tc5", &Tc5_Fixture );

  T_plan( 2 );

  Tc5_Action_0();
  Tc5_Action_1();

  T_case_end();
}

/** @} */

/**
 * @defgroup Tc6 spec:/tc6
 *
 * @ingroup Ts
 *
 * @{
 */

void Tc6_Run( void )
{
}

/** @} */

/**
 * @defgroup Tc7 spec:/tc7
 *
 * @ingroup Ts
 *
 * This test case performs the following actions:
 *
 * - Action.
 *
 * @{
 */

/**
 * @brief Action.
 */
static void Tc7_Action_0( void )
{
  /* 0 */
}

static T_fixture_node Tc7_Node;

static T_remark Tc7_Remark = {
  .next = NULL,
  .remark = "Tc7"
};

void Tc7_Run( void )
{
  (void) T_push_fixture( &Tc7_Node, &T_empty_fixture );

  T_plan( 1 );

  Tc7_Action_0();

  T_add_remark( &Tc7_Remark );
  T_pop_fixture();
}

/** @} */

/**
 * @defgroup Tc8 spec:/tc8
 *
 * @ingroup Ts
 *
 * This test case performs the following actions:
 *
 * - Action.
 *
 * @{
 */

/**
 * @brief Test context for spec:/tc8 test case.
 */
typedef struct {
  int member;
} Tc8_Context;

static Tc8_Context
  Tc8_Instance;

static T_fixture Tc8_Fixture = {
  .setup = NULL,
  .stop = NULL,
  .teardown = NULL,
  .scope = NULL,
  .initial_context = &Tc8_Instance
};

/**
 * @brief Action.
 */
static void Tc8_Action_0( void )
{
  /* 0 */
}

static T_fixture_node Tc8_Node;

static T_remark Tc8_Remark = {
  .next = NULL,
  .remark = "Tc8"
};

void Tc8_Run( void )
{
  (void) T_push_fixture( &Tc8_Node, &Tc8_Fixture );

  T_plan( 1 );

  Tc8_Action_0();

  T_add_remark( &Tc8_Remark );
  T_pop_fixture();
}

/** @} */

/**
 * @defgroup Tc9 spec:/tc9
 *
 * @ingroup Ts
 *
 * @brief Test case 9 brief description.
 *
 * Test case 9 description.
 *
 * This test case performs the following actions:
 *
 * - Test case 9 action 0 description.
 *
 * @{
 */

/**
 * @brief Test context for spec:/tc9 test case.
 */
typedef struct {
  /**
   * @brief Context 9 member brief.
   *
   * Context 9 member description.
   */
  int member;
} Tc9_Context;

static Tc9_Context
  Tc9_Instance;

static T_fixture Tc9_Fixture = {
  .setup = NULL,
  .stop = NULL,
  .teardown = NULL,
  .scope = NULL,
  .initial_context = &Tc9_Instance
};

/**
 * @brief Test case 9 action 0 description.
 */
static void Tc9_Action_0( void )
{
  /* Test case 9 action 0 code */
}

/**
 * @fn void T_case_body_Tc9( void )
 */
T_TEST_CASE_FIXTURE( Tc9, &Tc9_Fixture )
{
  Tc9_Action_0();
}

/** @} */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "tc5.h"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup Tc5
 */

/*
 * Copyright (C) 2020 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

#ifndef _TC5_H
#define _TC5_H

#include <d.h>

#include "e.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @addtogroup Tc5
 *
 * @{
 */

/* Header code for Tc5_Run() */

/**
 * @brief Runs the parameterized test case.
 *
 * @param[in] a Parameter A description.
 *
 * @param b Parameter B description.
 *
 * @param[out] c Parameter C description.
 */
void Tc5_Run( int *a, int b, int *c );

/** @} */

#ifdef __cplusplus
}
#endif

#endif /* _TC5_H */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "tc6.h"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup Tc6
 */

/*
 * Copyright (C) 2020 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

#ifndef _TC6_H
#define _TC6_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @addtogroup Tc6
 *
 * @{
 */

/**
 * @brief Runs the parameterized test case.
 */
void Tc6_Run( void );

/** @} */

#ifdef __cplusplus
}
#endif

#endif /* _TC6_H */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "action2.h"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup Action2
 */

/*
 * Copyright (C) 2020 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

#ifndef _ACTION2_H
#define _ACTION2_H

#include <d.h>

#include "e.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @addtogroup Action2
 *
 * @{
 */

typedef enum {
  Action2_Pre_A_A0,
  Action2_Pre_A_A1,
  Action2_Pre_A_NA
} Action2_Pre_A;

typedef enum {
  Action2_Pre_B_B0,
  Action2_Pre_B_B1,
  Action2_Pre_B_B2,
  Action2_Pre_B_NA
} Action2_Pre_B;

typedef enum {
  Action2_Pre_C_C0,
  Action2_Pre_C_C1,
  Action2_Pre_C_C2,
  Action2_Pre_C_NA
} Action2_Pre_C;

typedef enum {
  Action2_Post_A_A0,
  Action2_Post_A_A1,
  Action2_Post_A_A2,
  Action2_Post_A_A3,
  Action2_Post_A_NA
} Action2_Post_A;

typedef enum {
  Action2_Post_B_B0,
  Action2_Post_B_B1,
  Action2_Post_B_B2,
  Action2_Post_B_NA
} Action2_Post_B;

/* Header code for Action 2 with Action2_Run() */

/**
 * @brief Runs the parameterized test case.
 *
 * @param[in] a Parameter A description.
 *
 * @param b Parameter B description.
 *
 * @param[out] c Parameter C description.
 */
void Action2_Run( int *a, int b, int *c );

/** @} */

#ifdef __cplusplus
}
#endif

#endif /* _ACTION2_H */
"""
        assert content == src.read()
    with open(os.path.join(base_directory, "action2.c"), "r") as src:
        content = """/* SPDX-License-Identifier: BSD-2-Clause */

/**
 * @file
 *
 * @ingroup Action2
 */

/*
 * Copyright (C) 2020 embedded brains GmbH & Co. KG
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * This file was automatically generated.  Do not edit it.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <a.h>

#include "b.h"

#include <rtems/test.h>

/**
 * @defgroup Action2 spec:/action2
 *
 * @ingroup Ts
 *
 * @brief Test brief.
 *
 * Test description.
 *
 * @{
 */

typedef struct {
  uint16_t Skip : 1;
  uint16_t Pre_A_NA : 1;
  uint16_t Pre_B_NA : 1;
  uint16_t Pre_C_NA : 1;
  uint16_t Post_A : 3;
  uint16_t Post_B : 2;
} Action2_Entry;

/* Context support code */

/**
 * @brief Test context for spec:/action2 test case.
 */
typedef struct {
  /**
   * @brief Context member brief.
   *
   * Context member description.
   */
  int member;

  /**
   * @brief This member contains a copy of the corresponding Action2_Run()
   *   parameter.
   */
  int *a;

  /**
   * @brief This member contains a copy of the corresponding Action2_Run()
   *   parameter.
   */
  int b;

  /**
   * @brief This member contains a copy of the corresponding Action2_Run()
   *   parameter.
   */
  int *c;

  struct {
    /**
     * @brief This member defines the pre-condition indices for the next
     *   action.
     */
    size_t pci[ 3 ];

    /**
     * @brief This member defines the pre-condition states for the next action.
     */
    size_t pcs[ 3 ];

    /**
     * @brief If this member is true, then the test action loop is executed.
     */
    bool in_action_loop;

    /**
     * @brief This member contains the next transition map index.
     */
    size_t index;

    /**
     * @brief This member contains the current transition map entry.
     */
    Action2_Entry entry;

    /**
     * @brief If this member is true, then the current transition variant
     *   should be skipped.
     */
    bool skip;
  } Map;
} Action2_Context;

static Action2_Context
  Action2_Instance;

static const char * const Action2_PreDesc_A[] = {
  "A0",
  "A1",
  "NA"
};

static const char * const Action2_PreDesc_B[] = {
  "B0",
  "B1",
  "B2",
  "NA"
};

static const char * const Action2_PreDesc_C[] = {
  "C0",
  "C1",
  "C2",
  "NA"
};

static const char * const * const Action2_PreDesc[] = {
  Action2_PreDesc_A,
  Action2_PreDesc_B,
  Action2_PreDesc_C,
  NULL
};

/* Support code */

Action2_Context *instance = &Action2_Instance;

static const char ident[] = "Action2";

static void Action2_Pre_A_Prepare( Action2_Context *ctx, Action2_Pre_A state )
{
  /* Pre A prologue. */

  switch ( state ) {
    case Action2_Pre_A_A0: {
      /*
       * Pre A 0.
       */
      /* Pre A 0 */
      break;
    }

    case Action2_Pre_A_A1: {
      /*
       * Pre A 1.
       */
      /* Pre A 1 */
      ctx->Map.skip = true;
      break;
    }

    case Action2_Pre_A_NA:
      break;
  }

  /* Pre A epilogue. */
}

static void Action2_Pre_B_Prepare( Action2_Pre_B state )
{
  /* Pre B prologue. */

  switch ( state ) {
    case Action2_Pre_B_B0: {
      /*
       * Pre B 0.
       */
      /* Pre B 0 */
      break;
    }

    case Action2_Pre_B_B1: {
      /*
       * Pre B 1.
       */
      /* Pre B 1 */
      break;
    }

    case Action2_Pre_B_B2: {
      /*
       * Pre B 1.
       */
      /* Pre B 1 */
      break;
    }

    case Action2_Pre_B_NA:
      break;
  }

  /* Pre B epilogue. */
}

static void Action2_Pre_C_Prepare( Action2_Pre_C state )
{
  /* Pre C prologue. */

  switch ( state ) {
    case Action2_Pre_C_C0: {
      /*
       * Pre C 0.
       */
      /* Pre C 0 */
      break;
    }

    case Action2_Pre_C_C1: {
      /*
       * Pre C 1.
       */
      /* Pre B 1 */
      break;
    }

    case Action2_Pre_C_C2: {
      /*
       * Pre C 2.
       */
      /* Pre C 2 */
      break;
    }

    case Action2_Pre_C_NA:
      break;
  }

  /* Pre C epilogue. */
}

static void Action2_Post_A_Check( Action2_Post_A state )
{
  /* Post A prologue. */

  switch ( state ) {
    case Action2_Post_A_A0: {
      /*
       * Post A 0.
       */
      /* Post A 0 */
      break;
    }

    case Action2_Post_A_A1: {
      /*
       * Post A 1.
       */
      /* Post A 1 */
      break;
    }

    case Action2_Post_A_A2: {
      /*
       * Post A 2.
       */
      /* Post A 2 */
      break;
    }

    case Action2_Post_A_A3: {
      /*
       * Post A 3.
       */
      /* Post A 3 */
      break;
    }

    case Action2_Post_A_NA:
      break;
  }

  /* Post A epilogue. */
}

static void Action2_Post_B_Check( Action2_Post_B state )
{
  /* Post B prologue. */

  switch ( state ) {
    case Action2_Post_B_B0: {
      /*
       * Post B 0.
       */
      /* Post B 0 */
      break;
    }

    case Action2_Post_B_B1: {
      /*
       * Post B 1.
       */
      /* Post B 1 */
      break;
    }

    case Action2_Post_B_B2: {
      /*
       * Post B 2.
       */
      /* Post B 2 */
      break;
    }

    case Action2_Post_B_NA:
      break;
  }

  /* Post B epilogue. */
}

/**
 * @brief Setup brief.
 *
 * Setup description.
 */
static void Action2_Setup( void )
{
  /* Setup code */
}

static void Action2_Setup_Wrap( void *arg )
{
  Action2_Context *ctx;

  ctx = arg;
  ctx->Map.in_action_loop = false;
  Action2_Setup();
}

/**
 * @brief Teardown brief.
 *
 * Teardown description.
 */
static void Action2_Teardown( void )
{
  /* Teardown code */
}

static void Action2_Teardown_Wrap( void *arg )
{
  Action2_Context *ctx;

  ctx = arg;
  ctx->Map.in_action_loop = false;
  Action2_Teardown();
}

static void Action2_Prepare( void )
{
  /* Prepare */
}

static void Action2_Action( Action2_Context *ctx )
{
  /* Action with ctx */
}

static void Action2_Cleanup( void )
{
  /* Cleanup */
}

static const Action2_Entry
Action2_Entries[] = {
  { 0, 1, 0, 0, Action2_Post_A_A1, Action2_Post_B_NA },
  { 0, 0, 0, 0, Action2_Post_A_A2, Action2_Post_B_B0 },
  { 1, 0, 0, 0, Action2_Post_A_NA, Action2_Post_B_NA },
  { 0, 0, 0, 0, Action2_Post_A_A1, Action2_Post_B_B0 },
#if defined(BOOM)
  { 0, 1, 0, 0, Action2_Post_A_NA, Action2_Post_B_B0 },
#else
  { 0, 0, 0, 0, Action2_Post_A_A1, Action2_Post_B_B0 },
#endif
#if defined(BOOM)
  { 0, 1, 0, 0, Action2_Post_A_NA, Action2_Post_B_B0 },
#else
  { 0, 0, 0, 0, Action2_Post_A_A2, Action2_Post_B_B0 },
#endif
  { 0, 0, 0, 0, Action2_Post_A_A3, Action2_Post_B_B0 }
};

static const uint8_t
Action2_Map[] = {
  4, 3, 3, 0, 0, 0, 1, 1, 1, 5, 1, 6, 0, 0, 0, 2, 2, 2
};

static size_t Action2_Scope( void *arg, char *buf, size_t n )
{
  Action2_Context *ctx;

  ctx = arg;

  if ( ctx->Map.in_action_loop ) {
    return T_get_scope( Action2_PreDesc, buf, n, ctx->Map.pcs );
  }

  return 0;
}

static T_fixture Action2_Fixture = {
  .setup = Action2_Setup_Wrap,
  .stop = NULL,
  .teardown = Action2_Teardown_Wrap,
  .scope = Action2_Scope,
  .initial_context = &Action2_Instance
};

static const uint8_t Action2_Weights[] = {
  9, 3, 1
};

static void Action2_Skip( Action2_Context *ctx, size_t index )
{
  switch ( index + 1 ) {
    case 1:
      ctx->Map.pci[ 1 ] = Action2_Pre_B_NA - 1;
      /* Fall through */
    case 2:
      ctx->Map.pci[ 2 ] = Action2_Pre_C_NA - 1;
      break;
  }
}

static inline Action2_Entry Action2_PopEntry( Action2_Context *ctx )
{
  size_t index;

  if ( ctx->Map.skip ) {
    size_t i;

    ctx->Map.skip = false;
    index = 0;

    for ( i = 0; i < 3; ++i ) {
      index += Action2_Weights[ i ] * ctx->Map.pci[ i ];
    }
  } else {
    index = ctx->Map.index;
  }

  ctx->Map.index = index + 1;

  return Action2_Entries[
    Action2_Map[ index ]
  ];
}

static void Action2_SetPreConditionStates( Action2_Context *ctx )
{
  if ( ctx->Map.entry.Pre_A_NA ) {
    ctx->Map.pcs[ 0 ] = Action2_Pre_A_NA;
  } else {
    ctx->Map.pcs[ 0 ] = ctx->Map.pci[ 0 ];
  }

  ctx->Map.pcs[ 1 ] = ctx->Map.pci[ 1 ];
  ctx->Map.pcs[ 2 ] = ctx->Map.pci[ 2 ];
}

static void Action2_TestVariant( Action2_Context *ctx )
{
  Action2_Pre_A_Prepare( ctx, ctx->Map.pcs[ 0 ] );

  if ( ctx->Map.skip ) {
    Action2_Skip( ctx, 0 );
    return;
  }

  Action2_Pre_B_Prepare( ctx->Map.pcs[ 1 ] );
  Action2_Pre_C_Prepare( ctx->Map.pcs[ 2 ] );
  Action2_Action( ctx );
  Action2_Post_A_Check( ctx->Map.entry.Post_A );
  Action2_Post_B_Check( ctx->Map.entry.Post_B );
}

static T_fixture_node Action2_Node;

static T_remark Action2_Remark = {
  .next = NULL,
  .remark = "Action2"
};

void Action2_Run( int *a, int b, int *c )
{
  Action2_Context *ctx;

  ctx = &Action2_Instance;
  ctx->a = a;
  ctx->b = b;
  ctx->c = c;

  ctx = T_push_fixture( &Action2_Node, &Action2_Fixture );
  ctx->Map.in_action_loop = true;
  ctx->Map.index = 0;
  ctx->Map.skip = false;

  for (
    ctx->Map.pci[ 0 ] = Action2_Pre_A_A0;
    ctx->Map.pci[ 0 ] < Action2_Pre_A_NA;
    ++ctx->Map.pci[ 0 ]
  ) {
    for (
      ctx->Map.pci[ 1 ] = Action2_Pre_B_B0;
      ctx->Map.pci[ 1 ] < Action2_Pre_B_NA;
      ++ctx->Map.pci[ 1 ]
    ) {
      for (
        ctx->Map.pci[ 2 ] = Action2_Pre_C_C0;
        ctx->Map.pci[ 2 ] < Action2_Pre_C_NA;
        ++ctx->Map.pci[ 2 ]
      ) {
        ctx->Map.entry = Action2_PopEntry( ctx );

        if ( ctx->Map.entry.Skip ) {
          continue;
        }

        Action2_SetPreConditionStates( ctx );
        Action2_Prepare();
        Action2_TestVariant( ctx );
        Action2_Cleanup();
      }
    }
  }

  T_add_remark( &Action2_Remark );
  T_pop_fixture();
}

/** @} */
"""
        assert content == src.read()


def _add_item(item_cache, uid, data, item_type):
    item = Item(item_cache, uid, data)
    item.type = item_type
    item_cache[item.uid] = item
    return item


def test_validation_invalid_actions(tmpdir):
    item_cache = EmptyItemCache(SpecWareTypeProvider({}))
    validation_config = {
        "base-directory-map": [{
            "source": "/foobar/spec",
            "target": tmpdir
        }]
    }
    spdx = "CC-BY-SA-4.0 OR BSD-2-Clause"
    copyright = "Copyright (C) 2021 John Doe"
    action_data = {
        "SPDX-License-Identifier":
        spdx,
        "copyrights": [copyright],
        "enabled-by":
        True,
        "functional-type":
        "action",
        "links": [],
        "post-conditions": [{
            "name": "X",
            "states": [],
            "test-epilogue": None,
            "test-prologue": None,
        }],
        "pre-conditions": [{
            "name": "A",
            "states": [],
            "test-epilogue": None,
            "test-prologue": None,
        }],
        "rationale":
        None,
        "references": [],
        "requirement-type":
        "functional",
        "skip-reasons": {},
        "test-action":
        None,
        "test-brief":
        None,
        "test-cleanup":
        None,
        "test-context": [],
        "test-context-support":
        None,
        "test-description":
        None,
        "test-header":
        None,
        "test-includes": [],
        "test-local-includes": [],
        "test-name":
        "A",
        "test-prepare":
        None,
        "test-setup":
        None,
        "test-stop":
        None,
        "test-support":
        None,
        "test-target":
        "a.c",
        "test-teardown":
        None,
        "text":
        None,
        "transition-map": [{
            "enabled-by": True,
            "post-conditions": {
                "X": "X0",
            },
            "pre-conditions": {
                "A": "all"
            },
        }],
        "type":
        "requirement",
    }
    _add_item(item_cache, "/a", action_data, "requirement/functional/action")
    match = ("the source file 'a.c' is not a source file of an "
             "item of type 'build/test-program'")
    with pytest.raises(ValueError, match=match):
        generate_validation(validation_config, item_cache)
    test_program_data = {
        "SPDX-License-Identifier": spdx,
        "copyrights": [copyright],
        "build-type": "test-program",
        "enabled-by": True,
        "links": [],
        "source": ["a.c"],
        "type": "build",
    }
    _add_item(item_cache, "/tp", test_program_data, "build/test-program")
    match = "pre-condition 'A' of spec:/a has no states"
    with pytest.raises(ValueError, match=match):
        generate_validation(validation_config, item_cache)
    action_data["pre-conditions"][0]["states"] = [{
        "name": "A0",
        "test-code": None,
        "text": None
    }]
    match = ("transition map descriptor 0 of spec:/a refers to non-existent "
             "post-condition state 'X0'")
    with pytest.raises(ValueError, match=match):
        generate_validation(validation_config, item_cache)
    action_data["post-conditions"][0]["states"] = [{
        "name": "X0",
        "test-code": None,
        "text": None
    }]
    action_data["transition-map"][0]["pre-conditions"]["A"] = ["a"]
    match = ("transition map descriptor 0 of spec:/a refers to non-existent "
             "state 'a' of pre-condition 'A'")
    with pytest.raises(ValueError, match=match):
        generate_validation(validation_config, item_cache)
    action_data["transition-map"][0]["pre-conditions"]["A"] = ["A0"]
    action_data["transition-map"].append({
        "enabled-by": True,
        "post-conditions": {
            "X": "X0",
        },
        "pre-conditions": {
            "A": "all"
        },
    })
    match = ("transition map descriptor 1 of spec:/a duplicates pre-condition "
             "set {A=A0} defined by transition map descriptor 0")
    with pytest.raises(ValueError, match=match):
        generate_validation(validation_config, item_cache)
    action_data["transition-map"][1]["pre-conditions"]["A"] = ["A1"]
    action_data["pre-conditions"][0]["states"].append({
        "name": "A1",
        "test-code": None,
        "text": None
    })
    action_data["pre-conditions"][0]["states"].append({
        "name": "A2",
        "test-code": None,
        "text": None
    })
    match = ("transition map of spec:/a contains no default entry "
             "for pre-condition set {A=A2}")
    with pytest.raises(ValueError, match=match):
        generate_validation(validation_config, item_cache)
    action_data["transition-map"][0]["enabled-by"] = False
    match = ("transition map descriptor 0 of spec:/a is the first "
             "variant for {A=A0} and it is not enabled by default")
    with pytest.raises(ValueError, match=match):
        generate_validation(validation_config, item_cache)
    action_data["transition-map"][0]["enabled-by"] = True
    action_data["transition-map"][-1]["post-conditions"]["X"] = []
    match = ("cannot determine state for post-condition 'X' of transition map "
             "descriptor 1 of spec:/a for pre-condition set {A=A1}")
    with pytest.raises(ValueError, match=match):
        generate_validation(validation_config, item_cache)
