import {guard} from "@/lib/guard";
import {ParentSpace} from "@/components/parent";
export default async function Page(){await guard("parent");return <ParentSpace/>;}
