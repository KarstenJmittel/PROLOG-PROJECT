:- dynamic incident_location/2.
:- dynamic report/3.
:- dynamic feeds/2.

substation(substation_central).
substation(substation_north).

feeder(feeder_alpha).
feeder(feeder_beta).
feeder(feeder_gamma).

transformer(transformer_a1).
transformer(transformer_a2).
transformer(transformer_b1).
transformer(transformer_c1).

zone(residential_zone_1).
zone(commercial_district).
zone(industrial_park).
zone(hospital_hub).

feeds(substation_central, feeder_alpha).
feeds(substation_central, feeder_beta).
feeds(substation_north, feeder_gamma).

feeds(feeder_alpha, transformer_a1).
feeds(feeder_alpha, transformer_a2).
feeds(feeder_beta, transformer_b1).
feeds(feeder_gamma, transformer_c1).

feeds(transformer_a1, residential_zone_1).
feeds(transformer_a2, commercial_district).
feeds(transformer_b1, industrial_park).
feeds(transformer_c1, hospital_hub).

priority(hospital_hub, critical).
priority(industrial_park, high).
priority(commercial_district, medium).
priority(residential_zone_1, standard).

supplies(Upstream, Downstream) :-
    feeds(Upstream, Downstream).
supplies(Upstream, Downstream) :-
    feeds(Upstream, Intermediate),
    supplies(Intermediate, Downstream).

upstream_source(Downstream, Upstream) :-
    supplies(Upstream, Downstream).

upstream_chain(Node, [Node]) :-
    \+ feeds(_, Node), !.
upstream_chain(Node, [Node | Path]) :-
    feeds(Parent, Node),
    upstream_chain(Parent, Path), !.

downstream_zone(Node, Zone) :-
    zone(Node),
    Zone = Node.
downstream_zone(Node, Zone) :-
    supplies(Node, Zone),
    zone(Zone).

suspect_component(Incident, Feeder) :-
    diagnose_fault(Incident, 'FEEDER FAULT'),
    incident_location(Incident, Loc),
    (feeder(Loc) -> Feeder = Loc ; (supplies(Feeder, Loc), feeder(Feeder))), !.
suspect_component(Incident, Transformer) :-
    diagnose_fault(Incident, 'TRANSFORMER FAULT'),
    incident_location(Incident, Loc),
    (transformer(Loc) -> Transformer = Loc ; (supplies(Transformer, Loc), transformer(Transformer))), !.
suspect_component(Incident, Loc) :-
    incident_location(Incident, Loc), !.
suspect_component(_Incident, unknown).

incident_severity(Incident, 'CRITICAL') :-
    incident_location(Incident, Loc),
    priority(Loc, critical), !.
incident_severity(Incident, 'HIGH') :-
    incident_location(Incident, Loc),
    priority(Loc, high), !.
incident_severity(Incident, 'HIGH') :-
    diagnose_fault(Incident, 'FEEDER FAULT'), !.
incident_severity(_Incident, 'STANDARD').

diagnose_fault(Incident, 'FEEDER FAULT') :-
    report(Incident, control_room, feeder_trip),
    report(Incident, citizen, power_outage), !.

diagnose_fault(Incident, 'FALLEN LINE / POLE') :-
    report(Incident, citizen, sparks_on_pole),
    report(Incident, engineer, broken_wire), !.

diagnose_fault(Incident, 'TRANSFORMER FAULT') :-
    report(Incident, engineer, transformer_abnormal),
    report(Incident, citizen, power_outage), !.

diagnose_fault(Incident, 'INDUSTRIAL GRID OVERLOAD') :-
    report(Incident, factory, power_outage),
    report(Incident, factory, sparks_on_pole), !.

diagnose_fault(Incident, 'INDUSTRIAL TRANSFORMER SURGE') :-
    report(Incident, factory, power_outage),
    report(Incident, control_room, feeder_trip), !.

diagnose_fault(Incident, 'FACTORY SECTOR ISOLATION') :-
    report(Incident, factory, broken_wire),
    report(Incident, engineer, transformer_abnormal), !.

diagnose_fault(_Incident, 'UNKNOWN FAULT - INSUFFICIENT EVIDENCE').

recommend_action(Incident, 'CRITICAL: Dispatch emergency crew and activate hospital backup generator') :-
    incident_location(Incident, Loc),
    priority(Loc, critical), !.
recommend_action(Incident, 'Isolate tripped feeder breaker and switch to alternate feeder') :-
    diagnose_fault(Incident, 'FEEDER FAULT'), !.
recommend_action(Incident, 'Dispatch maintenance unit to inspect and replace transformer coils') :-
    diagnose_fault(Incident, 'TRANSFORMER FAULT'), !.
recommend_action(Incident, 'De-energize section and repair high-voltage line conductor') :-
    diagnose_fault(Incident, 'FALLEN LINE / POLE'), !.
recommend_action(Incident, 'Shed industrial load and balance substation distribution') :-
    diagnose_fault(Incident, 'INDUSTRIAL GRID OVERLOAD'), !.
recommend_action(Incident, 'Isolate industrial spur and inspect transformer surge protection') :-
    diagnose_fault(Incident, 'INDUSTRIAL TRANSFORMER SURGE'), !.
recommend_action(Incident, 'Isolate factory sector and rewire local distribution feed') :-
    diagnose_fault(Incident, 'FACTORY SECTOR ISOLATION'), !.
recommend_action(_Incident, 'Deploy field survey team to verify reports').