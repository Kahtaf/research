"""Pinned Ninja 1.12.1 environment/presence regressions; no native engine."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_capture import TMP
from test_provenance import SmallGraph
from safeio import Refusal
from provenance import copy_source

CP='rule cp\n  command = cp $in $out\n'
BUILD='build out/a: cp src/a\n'
DD='out/extra.dd'

class SmallFixtureCase(unittest.TestCase):
    def graph(self,text,extras=None):
        tmp=tempfile.TemporaryDirectory(dir=TMP);self.addCleanup(tmp.cleanup)
        f=SmallGraph(tmp.name,text,extras);self.addCleanup(f.close);return f
    def edge(self,text,extras=None):return self.graph(text,extras).graph.edge('out/a')

class EffectiveBindingsTests(SmallFixtureCase):
    def test_file_own_command_wins_without_build_environment(self):
        edge=self.edge('command = echo unreviewed\n'+CP+BUILD)
        self.assertEqual(edge['command'],'echo unreviewed');self.assertFalse(edge['has_build_environment'])
        self.assertEqual(edge['effective_binding_sources']['command'],'file-own')
        with self.assertRaisesRegex(Refusal,'PRODUCER_COMMAND'):copy_source(edge)
    def test_file_own_defined_empty_command_shadows_rule(self):
        edge=self.edge('command =\n'+CP+BUILD)
        self.assertEqual(edge['command'],'');self.assertEqual(edge['effective_binding_sources']['command'],'file-own')
        with self.assertRaisesRegex(Refusal,'PRODUCER_COMMAND'):copy_source(edge)
    def test_unrelated_binding_creates_environment_and_rule_precedes_parent(self):
        edge=self.edge('command = echo unreviewed\n'+CP+BUILD+'  unused = value\n')
        self.assertTrue(edge['has_build_environment']);self.assertEqual(copy_source(edge),'src/a')
        self.assertEqual(edge['effective_binding_sources']['command'],'rule')
    def test_defined_empty_unrelated_binding_still_creates_environment(self):
        edge=self.edge('command = echo unreviewed\n'+CP+BUILD+'  unused =\n')
        self.assertTrue(edge['has_build_environment']);self.assertEqual(copy_source(edge),'src/a')
    def test_comments_and_blanks_do_not_create_environment(self):
        edge=self.edge('command = echo unreviewed\n'+CP+BUILD+'  # only comment\n  \n')
        self.assertFalse(edge['has_build_environment']);self.assertEqual(edge['command'],'echo unreviewed')
    def test_local_empty_command_wins_over_file_and_rule(self):
        edge=self.edge('command = echo file\n'+CP+BUILD+'  command =\n')
        self.assertTrue(edge['has_build_environment']);self.assertEqual(edge['command'],'')
        self.assertEqual(edge['effective_binding_sources']['command'],'build-own')
        with self.assertRaisesRegex(Refusal,'PRODUCER_COMMAND'):copy_source(edge)
    def test_local_literal_command_wins_over_file_and_rule(self):
        edge=self.edge('command = echo file\nrule cp\n  command = echo rule\n'+BUILD+'  command = cp src/a out/a\n')
        self.assertEqual(copy_source(edge),'src/a');self.assertEqual(edge['effective_binding_sources']['command'],'build-own')
    def test_local_command_is_eager_and_not_rescanned_with_builtins(self):
        edge=self.edge(CP+BUILD+'  command = cp $in $out\n')
        self.assertEqual(edge['command'],'cp  ')
        with self.assertRaisesRegex(Refusal,'PRODUCER_COMMAND'):copy_source(edge)
    def test_builtin_in_out_precede_own_bindings(self):
        edge=self.edge('in = file\nout = file\n'+CP+BUILD+'  in = local\n  out = local\n')
        self.assertEqual(edge['command'],'cp src/a out/a');self.assertEqual(copy_source(edge),'src/a')
    def test_enclosing_parent_command_does_not_override_child_rule(self):
        edge=self.edge('command = echo parent\n'+CP+'subninja out/child.ninja\n',{'child.ninja':BUILD})
        self.assertFalse(edge['has_build_environment']);self.assertEqual(copy_source(edge),'src/a')
    def test_child_own_command_overrides_inherited_rule(self):
        edge=self.edge(CP+'subninja out/child.ninja\n',{'child.ninja':'command = echo child\n'+BUILD})
        self.assertEqual(edge['command'],'echo child')
        with self.assertRaisesRegex(Refusal,'PRODUCER_COMMAND'):copy_source(edge)
    def test_shared_include_binding_is_an_own_binding(self):
        edge=self.edge(CP+'include out/shared.ninja\n'+BUILD,{'shared.ninja':'command = echo included\n'})
        self.assertEqual(edge['command'],'echo included');self.assertEqual(edge['effective_binding_sources']['command'],'file-own')
    def test_later_own_command_assignment_is_visible_at_command_time(self):
        edge=self.edge(CP+BUILD+'command = echo later\n')
        self.assertEqual(edge['command'],'echo later')
        with self.assertRaisesRegex(Refusal,'PRODUCER_COMMAND'):copy_source(edge)
    def test_empty_file_own_description_shadows_rule_without_edge_environment(self):
        edge=self.edge('description =\nrule cp\n  command = echo [$description]\n  description = rule\n'+BUILD)
        self.assertEqual(edge['command'],'echo []');self.assertEqual(edge['rule_bindings']['description'],'')
    def test_new_environment_restores_rule_description_before_enclosing_empty(self):
        edge=self.edge('description =\nrule cp\n  command = echo [$description]\n  description = rule\n'+BUILD+'  unused =\n')
        self.assertEqual(edge['command'],'echo [rule]')
    def test_defined_empty_enclosing_parent_does_not_override_rule(self):
        edge=self.edge('command =\n'+CP+'subninja out/child.ninja\n',{'child.ninja':BUILD})
        self.assertEqual(copy_source(edge),'src/a')
    def test_eager_file_literal_dollar_is_not_rescanned(self):
        edge=self.edge('command = echo $$literal\n'+CP+BUILD)
        self.assertEqual(edge['command'],'echo $literal')
    def test_own_command_can_override_unused_cyclic_rule_command(self):
        edge=self.edge('command = cp src/a out/a\nrule cp\n  command = $description\n  description = $command\n'+BUILD)
        self.assertEqual(copy_source(edge),'src/a')
    def test_parent_command_cannot_break_rule_cycle_when_edge_environment_exists(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_VARIABLE'):
            self.edge('command = cp src/a out/a\nrule cp\n  command = $description\n  description = $command\n'+BUILD+'  unused =\n')

class EffectiveDyndepTests(SmallFixtureCase):
    def test_rule_nonempty_dyndep_refuses(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_DYNDEP'):self.edge(CP+'  dyndep = '+DD+'\n'+BUILD)
    def test_local_nonempty_dyndep_refuses(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_DYNDEP'):self.edge(CP+BUILD+'  dyndep = '+DD+'\n')
    def test_own_file_dyndep_absent_from_rule_is_still_effective(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_DYNDEP'):self.edge('dyndep = '+DD+'\n'+CP+BUILD)
    def test_parent_file_dyndep_fallback_without_rule_binding_refuses(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_DYNDEP'):
            self.edge('dyndep = '+DD+'\n'+CP+'subninja out/child.ninja\n',{'child.ninja':BUILD})
    def test_local_empty_dyndep_shadows_nonempty_rule_and_file(self):
        edge=self.edge('dyndep = '+DD+'\n'+CP+'  dyndep = '+DD+'\n'+BUILD+'  dyndep =\n')
        self.assertEqual(copy_source(edge),'src/a');self.assertEqual(edge['rule_bindings']['dyndep'],'')
        self.assertEqual(edge['effective_binding_sources']['dyndep'],'build-own')
    def test_own_file_empty_dyndep_shadows_nonempty_rule(self):
        edge=self.edge('dyndep =\n'+CP+'  dyndep = '+DD+'\n'+BUILD)
        self.assertEqual(edge['rule_bindings']['dyndep'],'');self.assertEqual(edge['effective_binding_sources']['dyndep'],'file-own')
    def test_nonempty_own_file_dyndep_precedes_empty_rule_without_build_env(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_DYNDEP'):
            self.edge('dyndep = '+DD+'\n'+CP+'  dyndep =\n'+BUILD)
    def test_new_environment_rule_empty_dyndep_precedes_nonempty_parent(self):
        edge=self.edge('dyndep = '+DD+'\n'+CP+'  dyndep =\n'+BUILD+'  unused =\n')
        self.assertEqual(edge['rule_bindings']['dyndep'],'');self.assertEqual(edge['effective_binding_sources']['dyndep'],'rule')
    def test_parent_empty_dyndep_cannot_override_child_rule_nonempty(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_DYNDEP'):
            self.edge('dyndep =\n'+CP+'  dyndep = '+DD+'\nsubninja out/child.ninja\n',{'child.ninja':BUILD})
    def test_child_own_empty_dyndep_shadows_parent_and_rule(self):
        edge=self.edge('dyndep = '+DD+'\n'+CP+'  dyndep = '+DD+'\nsubninja out/child.ninja\n',{'child.ninja':'dyndep =\n'+BUILD})
        self.assertEqual(edge['rule_bindings']['dyndep'],'');self.assertEqual(edge['effective_binding_sources']['dyndep'],'file-own')
    def test_dyndep_is_parse_time_even_if_later_file_value_is_empty(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_DYNDEP'):
            self.edge('dyndep = '+DD+'\n'+CP+BUILD+'dyndep =\n')
    def test_later_file_dyndep_does_not_invent_parse_time_dependency(self):
        edge=self.edge('dyndep =\n'+CP+BUILD+'dyndep = '+DD+'\n')
        self.assertEqual(edge['rule_bindings']['dyndep'],'');self.assertEqual(edge['dyndep_evaluation'],'parse-time-unescaped')
    def test_local_dyndep_uses_eager_file_value(self):
        edge=self.edge(CP+BUILD+'  dyndep = $later\nlater = '+DD+'\n')
        self.assertEqual(edge['rule_bindings']['dyndep'],'')
    def test_nested_effective_binding_can_make_dyndep_nonempty(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_DYNDEP'):
            self.edge('description = '+DD+'\n'+CP+'  dyndep = $description\n  description =\n'+BUILD)
    def test_dyndep_cycle_and_malformed_expansion_refuse(self):
        with self.assertRaisesRegex(Refusal,'GRAPH_VARIABLE'):
            self.edge(CP+'  dyndep = $description\n  description = $dyndep\n'+BUILD)
        with self.assertRaisesRegex(Refusal,'GRAPH_SYNTAX'):self.edge(CP+'  dyndep = ${\n'+BUILD)
    def test_no_dyndep_payload_is_opened(self):
        f=self.graph(CP+'  dyndep = '+DD+'\n'+BUILD)
        with patch.object(f.tree,'open',side_effect=AssertionError('no payload access')) as opened:
            with self.assertRaisesRegex(Refusal,'GRAPH_DYNDEP'):f.graph.edge('out/a')
            opened.assert_not_called()
