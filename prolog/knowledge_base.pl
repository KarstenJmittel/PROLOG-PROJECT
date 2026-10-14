% ==============================================================================
%                    GRIDRESCUE - PROLOG KNOWLEDGE BASE
%              Electrical Power Grid Expert Decision Support System
% ==============================================================================

% ------------------------------------------------------------------------------
% 1. DYNAMIC PREDICATES
% Facts that are added dynamically per incident from database reports and locations.
% ------------------------------------------------------------------------------
:- dynamic incident_location/2.  % incident_location(IncidentId, LocationName)
:- dynamic report/3.             % report(IncidentId, SourceType, EvidenceCategory)
:- dynamic feeds/2.              % feeds(UpstreamNode, DownstreamNode)


% ------------------------------------------------------------------------------
% 2. GRID INFRASTRUCTURE FACTS
% Physical assets in the power distribution network.
% ------------------------------------------------------------------------------

% Substations (High-voltage transmission input)
substation(substation_central).
substation(substation_north).

% Feeders (Medium-voltage distribution lines)
feeder(feeder_alpha).
feeder(feeder_beta).
feeder(feeder_gamma).

% Transformers (Step-down units supplying local sectors)
transformer(transformer_a1).
transformer(transformer_a2).
transformer(transformer_b1).
transformer(transformer_c1).

% Consumer Zones (End-use destination sectors)
zone(residential_zone_1).
zone(commercial_district).
zone(industrial_park).
zone(hospital_hub).


% ------------------------------------------------------------------------------
% 3. GRID TOPOLOGY (ELECTRICAL DISTRIBUTION GRAPH)
% Models the power flow: Substation -> Feeder -> Transformer -> Zone
% ------------------------------------------------------------------------------

% Substations feed Feeders:
feeds(substation_central, feeder_alpha).
feeds(substation_central, feeder_beta).
feeds(substation_north,   feeder_gamma).

% Feeders feed Transformers:
feeds(feeder_alpha, transformer_a1).
feeds(feeder_alpha, transformer_a2).
feeds(feeder_beta,  transformer_b1).
feeds(feeder_gamma, transformer_c1).

% Transformers feed Consumer Zones:
feeds(transformer_a1, residential_zone_1).
feeds(transformer_a2, commercial_district).
feeds(transformer_b1, industrial_park).
feeds(transformer_c1, hospital_hub).


% ------------------------------------------------------------------------------
% 4. ZONE PRIORITY LEVELS
% Establishes emergency response urgency for different sectors.
% ------------------------------------------------------------------------------
priority(hospital_hub,        critical).
priority(industrial_park,     high).
priority(commercial_district, medium).
priority(residential_zone_1,  standard).


% ------------------------------------------------------------------------------
% 5. RECURSIVE POWER CHAIN REASONING
% Traces electrical power paths up and down the grid.
% ------------------------------------------------------------------------------

% Node A supplies Node B if it directly feeds it, or feeds an intermediate node.
supplies(Upstream, Downstream) :-
    feeds(Upstream, Downstream).
supplies(Upstream, Downstream) :-
    feeds(Upstream, Intermediate),
    supplies(Intermediate, Downstream).

% An Upstream source is any parent supplying a downstream node.
upstream_source(Downstream, Upstream) :-
    supplies(Upstream, Downstream).

% upstream_chain(Node, Chain): Computes full ancestral path to root substation.
upstream_chain(Node, [Node]) :-
    \+ feeds(_, Node), !.
upstream_chain(Node, [Node | Path]) :-
    feeds(Parent, Node),
    upstream_chain(Parent, Path), !.

% downstream_zone(Node, Zone): Identifies affected end-consumer zones.
downstream_zone(Node, Zone) :-
    zone(Node),
    Zone = Node.
downstream_zone(Node, Zone) :-
    supplies(Node, Zone),
    zone(Zone).


% ------------------------------------------------------------------------------
% 6. FAULT DIAGNOSIS RULES
% Correlates evidence from multiple parties to deduce the root failure.
% ------------------------------------------------------------------------------

% Rule 1: Feeder breaker trip verified by citizen power outage
diagnose_fault(Incident, 'FEEDER FAULT') :-
    report(Incident, control_room, feeder_trip),
    report(Incident, citizen, power_outage), !.

% Rule 2: Sparking utility pole confirmed by field engineer broken wire
diagnose_fault(Incident, 'FALLEN LINE / POLE') :-
    report(Incident, citizen, sparks_on_pole),
    report(Incident, engineer, broken_wire), !.

% Rule 3: Abnormal transformer telemetry confirmed by local blackout
diagnose_fault(Incident, 'TRANSFORMER FAULT') :-
    report(Incident, engineer, transformer_abnormal),
    report(Incident, citizen, power_outage), !.

% Rule 4: Factory blackout coupled with sparking utility line
diagnose_fault(Incident, 'INDUSTRIAL GRID OVERLOAD') :-
    report(Incident, factory, power_outage),
    report(Incident, factory, sparks_on_pole), !.

% Rule 5: Factory outage correlated with feeder breaker trip
diagnose_fault(Incident, 'INDUSTRIAL TRANSFORMER SURGE') :-
    report(Incident, factory, power_outage),
    report(Incident, control_room, feeder_trip), !.

% Rule 6: Factory wire damage paired with abnormal transformer reading
diagnose_fault(Incident, 'FACTORY SECTOR ISOLATION') :-
    report(Incident, factory, broken_wire),
    report(Incident, engineer, transformer_abnormal), !.

% Fallback: When reports are inconclusive or insufficient
diagnose_fault(_Incident, 'UNKNOWN FAULT - INSUFFICIENT EVIDENCE').


% ------------------------------------------------------------------------------
% 7. SUSPECT COMPONENT IDENTIFICATION
% Isolates the exact physical equipment causing the disruption.
% ------------------------------------------------------------------------------

% If a feeder fault is diagnosed, locate the feeder supplying the incident zone:
suspect_component(Incident, Feeder) :-
    diagnose_fault(Incident, 'FEEDER FAULT'),
    incident_location(Incident, Loc),
    (feeder(Loc) -> Feeder = Loc ; (supplies(Feeder, Loc), feeder(Feeder))), !.

% If a transformer fault is diagnosed, locate the transformer supplying the zone:
suspect_component(Incident, Transformer) :-
    diagnose_fault(Incident, 'TRANSFORMER FAULT'),
    incident_location(Incident, Loc),
    (transformer(Loc) -> Transformer = Loc ; (supplies(Transformer, Loc), transformer(Transformer))), !.

% Otherwise suspect the reported location itself:
suspect_component(Incident, Loc) :-
    incident_location(Incident, Loc), !.

% Default unknown
suspect_component(_Incident, unknown).


% ------------------------------------------------------------------------------
% 8. SEVERITY EVALUATION
% Determines the triage severity tier (CRITICAL, HIGH, STANDARD).
% ------------------------------------------------------------------------------

% Critical life-safety facilities (e.g. Hospital Hub)
incident_severity(Incident, 'CRITICAL') :-
    incident_location(Incident, Loc),
    priority(Loc, critical), !.

% High priority zones (e.g. Industrial Park)
incident_severity(Incident, 'HIGH') :-
    incident_location(Incident, Loc),
    priority(Loc, high), !.

% Major distribution trunk failure (Feeder trip)
incident_severity(Incident, 'HIGH') :-
    diagnose_fault(Incident, 'FEEDER FAULT'), !.

% Standard default severity
incident_severity(_Incident, 'STANDARD').


% ------------------------------------------------------------------------------
% 9. RECOMMENDED ACTION PLANS
% Generates prescriptive response protocols for grid dispatchers.
% ------------------------------------------------------------------------------

% Priority 1: Emergency life-safety protocol for hospitals
recommend_action(Incident, 'CRITICAL: Dispatch emergency crew and activate hospital backup generator') :-
    incident_location(Incident, Loc),
    priority(Loc, critical), !.

% Feeder isolation & rerouting
recommend_action(Incident, 'Isolate tripped feeder breaker and switch to alternate feeder') :-
    diagnose_fault(Incident, 'FEEDER FAULT'), !.

% Transformer maintenance
recommend_action(Incident, 'Dispatch maintenance unit to inspect and replace transformer coils') :-
    diagnose_fault(Incident, 'TRANSFORMER FAULT'), !.

% High-voltage conductor repair
recommend_action(Incident, 'De-energize section and repair high-voltage line conductor') :-
    diagnose_fault(Incident, 'FALLEN LINE / POLE'), !.

% Industrial balancing
recommend_action(Incident, 'Shed industrial load and balance substation distribution') :-
    diagnose_fault(Incident, 'INDUSTRIAL GRID OVERLOAD'), !.

% Industrial surge inspection
recommend_action(Incident, 'Isolate industrial spur and inspect transformer surge protection') :-
    diagnose_fault(Incident, 'INDUSTRIAL TRANSFORMER SURGE'), !.

% Sector rewiring
recommend_action(Incident, 'Isolate factory sector and rewire local distribution feed') :-
    diagnose_fault(Incident, 'FACTORY SECTOR ISOLATION'), !.

% Default standard response
recommend_action(_Incident, 'Deploy field survey team to verify reports').