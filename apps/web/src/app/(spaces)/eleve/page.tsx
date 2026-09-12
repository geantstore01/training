import {guard} from "@/lib/guard";
import {StudentSpace} from "@/components/student";
export default async function Page(){return <StudentSpace account={await guard("eleve")}/>;}
