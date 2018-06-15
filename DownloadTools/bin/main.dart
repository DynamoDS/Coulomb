import 'package:gcloud/datastore.dart' as ds;
import 'package:googleapis_auth/auth.dart' as auth;
import 'package:googleapis_auth/auth_io.dart' as auth_io;
import 'package:gcloud/src/datastore_impl.dart' as datastore_impl;
import 'package:gcloud/storage.dart' as storage;
import 'package:crypto/crypto.dart' as crypto;

import 'dart:math';
import 'dart:convert' as convert;
import 'dart:io' as io;
import 'dart:async';

String outputBasePath;
int hitCount = 0;
int newCount = 0;
int i = 0;
int seenSessions = 0;

var itemsToDelete = [];

var client;
var basePath;

main(List<String> args) async {
  if (args.length < 2) {
    print("Usage: downloader dynamoinstr_keyfile cmd");
    io.exit(1);
  }

  String tokenFilePath = args[0];
  String cmd = args[1];

  var scopes = <String>[]
    ..addAll(datastore_impl.DatastoreImpl.SCOPES)
    ..addAll(storage.Storage.SCOPES);

  client = await auth_io.clientViaServiceAccount(
      new auth.ServiceAccountCredentials.fromJson(
          new io.File(tokenFilePath).readAsStringSync()),
      scopes);

  if (cmd.toLowerCase() == "download") {
    // Download phase
    print("Downloading phase");
    var datastore = new datastore_impl.DatastoreImpl(client, 's~dynamoinstr');

    try {
      while (true) {
        var query = new ds.Query(
            kind: 'Datom',
            filters: [
              new ds.Filter(
                  ds.FilterRelation.GreatherThan,
                  'RandomToken-b75e7a7f-dc90-48a1-8637-dbc123175a4d',
                  new Random().nextDouble())
            ]
            //      ,orders : [new ds.Order(ds.OrderDirection.Decending, 'RandomToken-b75e7a7f-dc90-48a1-8637-dbc123175a4d')]
            ,
            limit: 50);
        var page = await datastore.query(query);

        await dumpDataFromPage(page, datastore);

        await new Future.delayed(new Duration(seconds: 1));
      }
    } catch (e, st) {
      print("Halting export due to error \n $e \n $st");
    }
  } else {
    print("Unknown command: $cmd");
    io.exit(1);
  }
}

dumpDataFromPage(dynamic p, datastore_impl.DatastoreImpl datastore) async {
  for (ds.Entity e in p.items) {
    await processEntity(e, datastore);
  }
  if (p.isLast) return;
  else {
    var next = await p.next();
    await dumpDataFromPage(next, datastore);
  }
}

processEntity(ds.Entity e, datastore_impl.DatastoreImpl datastore) async {
  String data = "${convert.JSON.encode(e.properties)}";
  print(data);

 itemsToDelete.add(e.key);

 if (itemsToDelete.length > 10) {
   await datastore.commit(deletes: itemsToDelete);
   itemsToDelete.clear();
 }
}
